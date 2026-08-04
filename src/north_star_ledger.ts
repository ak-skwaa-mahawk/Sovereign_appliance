import * as ecdsa from 'ecdsa';
import * as crypto from 'crypto';

// Sovereignty Claim Interface
interface SovereigntyClaim {
  uei: string;
  coordinates: [number, number];
  lineage: string;
  timestamp: number;
}

// EEG Phase State (from FPT)
interface PhaseState {
  vitality: number;
  epsilon_d: number;
  coherence: number;
}

// Ledger Entry
interface LedgerEntry {
  index: number;
  previousHash: string;
  claim: SovereigntyClaim;
  phaseState: PhaseState;
  hash: string;
  signature: string;
}

// Octagonal Geometric Validator (simplified: checks 8-point symmetry via hash)
function validateOctagonalGeometry(entry: LedgerEntry): boolean {
  const points = 8;
  const hashBuffer = Buffer.from(entry.hash, 'hex');
  let sum = 0;
  for (let i = 0; i < points; i++) {
    sum += hashBuffer[i % hashBuffer.length];
  }
  return sum % points === 0; // Symmetry check
}

// Ledger Class
class NorthStarLedger {
  private chain: LedgerEntry[] = [];
  private keyPair: any;

  constructor() {
    this.keyPair = ecdsa.generateKeyPair(); // Generate ECDSA key
    this.createGenesis();
  }

  private createGenesis() {
    const genesisClaim: SovereigntyClaim = {
      uei: 'GENESIS',
      coordinates: [0, 0],
      lineage: 'North Star Origin',
      timestamp: Date.now()
    };
    const genesisPhase: PhaseState = { vitality: 1, epsilon_d: 0, coherence: 1 };
    this.addEntry(genesisClaim, genesisPhase);
  }

  private calculateHash(entry: LedgerEntry): string {
    return crypto.createHash('sha256')
      .update(JSON.stringify(entry))
      .digest('hex');
  }

  addEntry(claim: SovereigntyClaim, phaseState: PhaseState): boolean {
    const previousHash = this.chain.length > 0 ? this.chain[this.chain.length - 1].hash : '0';
    const entry: LedgerEntry = {
      index: this.chain.length,
      previousHash,
      claim,
      phaseState,
      hash: '',
      signature: ''
    };
    entry.hash = this.calculateHash(entry);
    entry.signature = ecdsa.sign(entry.hash, this.keyPair.privateKey); // Sign

    if (!validateOctagonalGeometry(entry)) {
      return false; // Reject if geometry invalid
    }

    this.chain.push(entry);
    return true;
  }

  verifyChain(): boolean {
    for (let i = 1; i < this.chain.length; i++) {
      const current = this.chain[i];
      const previous = this.chain[i - 1];

      if (current.previousHash !== previous.hash) return false;
      if (current.hash !== this.calculateHash(current)) return false;
      if (!ecdsa.verify(current.hash, current.signature, this.keyPair.publicKey)) return false;
      if (!validateOctagonalGeometry(current)) return false;
    }
    return true;
  }

  getChain(): LedgerEntry[] {
    return this.chain;
  }
}

// Export for use
export { NorthStarLedger, SovereigntyClaim, PhaseState };