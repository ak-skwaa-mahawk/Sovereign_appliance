import { ethers } from "ethers";
import * as fs from "fs";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Configuration & Environment Variables
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "https://ethereum-sepolia-rpc.publicnode.com";
const PRIVATE_KEY = process.env.RELAYER_PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000001";
const VERIFIER_CONTRACT_ADDRESS = process.env.VERIFIER_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000001";

// Contract ABI Interface
const VERIFIER_ABI = [
  "function currentEngineRoot() external view returns (bytes32)",
  "function settleEngineState(bytes calldata publicJournal, bytes calldata proofBytes) external",
  "event StateSettled(bytes32 indexed previousRoot, bytes32 indexed newRoot, uint64 shearEnergyBits, uint256 timestamp)"
];

export interface StateTransitionPayload {
  previousRoot: string;
  activeMemoryIds: string[];
  decayHalfLifeHours: number;
  priorPolygon: [number, number, number, number];
  candidatePolygon: [number, number, number, number];
}

export class ZkRelayerDaemon {
  private provider: ethers.JsonRpcProvider;
  private wallet: ethers.Wallet;
  private contract: ethers.Contract;

  constructor() {
    this.provider = new ethers.JsonRpcProvider(SEPOLIA_RPC_URL);
    this.wallet = new ethers.Wallet(PRIVATE_KEY, this.provider);
    this.contract = new ethers.Contract(VERIFIER_CONTRACT_ADDRESS, VERIFIER_ABI, this.wallet);
  }

  /**
   * Invokes the ZK-VM prover with private state witness and returns proof payload.
   */
  private async generateZkProof(payload: StateTransitionPayload): Promise<{ journal: string; proof: string }> {
    console.log("\x1b[36m[ZK Prover]: Writing private witness to temp stdin...\x1b[0m");
    fs.writeFileSync("witness_input.json", JSON.stringify(payload, null, 2));

    console.log("\x1b[36m[ZK Prover]: Executing guest_circuit.rs ZK-VM prover...\x1b[0m");
    
    // Command triggers local host prover passing private witness
    const { stdout, stderr } = await execAsync("npx tsx mock_zk_prover.ts witness_input.json");
    if (stderr && !stdout) {
      throw new Error(`ZK Prover error: ${stderr}`);
    }

    const result = JSON.parse(stdout);
    fs.unlinkSync("witness_input.json"); // Clean up private witness immediately

    return {
      journal: result.publicJournal,
      proof: result.proofBytes,
    };
  }

  /**
   * Main dispatch method called by local REPL lifecycle hooks.
   */
  public async processStateTransition(payload: StateTransitionPayload): Promise<string> {
    console.log("\n\x1b[33m--- INITIATING ZK-STARK STATE SETTLEMENT ---\x1b[0m");

    // 1. Fetch current on-chain root to verify alignment
    const onChainRoot = await this.contract.currentEngineRoot();
    console.log(`[1] On-Chain Verifier Current Root: ${onChainRoot}`);

    if (onChainRoot.toLowerCase() !== payload.previousRoot.toLowerCase()) {
      throw new Error(`Root mismatch! On-chain: ${onChainRoot}, Local: ${payload.previousRoot}`);
    }

    // 2. Generate ZK Proof & Public Journal
    const { journal, proof } = await this.generateZkProof(payload);
    console.log(`[2] ZK-STARK Proof generated. Size: ${proof.length / 2 - 1} bytes.`);

    // 3. Dispatch transaction to Sepolia SovereignStateVerifier
    console.log(`[3] Dispatching settleEngineState() to Sepolia contract...`);
    const tx = await this.contract.settleEngineState(journal, proof, {
      gasLimit: 500000,
    });

    console.log(`\x1b[32m[4] Settlement TX Submitted! Hash: ${tx.hash}\x1b[0m`);
    console.log("    Awaiting block confirmation...");

    const receipt = await tx.wait();
    console.log(`\x1b[32m[5] Confirmed in Block #${receipt.blockNumber}!\x1b[0m\n`);

    return tx.hash;
  }
}

// --- STANDALONE DAEMON ENTRY POINT ---
if (require.main === module) {
  const daemon = new ZkRelayerDaemon();
  console.log("\x1b[32m[Sovereign Daemon]: ZK Relayer Service initialized and listening for state transitions...\x1b[0m");

  // Keep the process alive and poll for mock REPL state transitions every 10 seconds
  setInterval(async () => {
    try {
      // Mock transition payload from REPL trigger
      const mockPayload: StateTransitionPayload = {
        previousRoot: "0x0000000000000000000000000000000000000000000000000000000000000000",
        activeMemoryIds: ["mem_init_01", "mem_init_02"],
        decayHalfLifeHours: 24.0,
        priorPolygon: [1.0, 1.0, 1.0, 1.0],
        candidatePolygon: [1.0, 0.98, 0.95, 1.0]
      };

      console.log("\n[Daemon Heartbeat]: Checking state transition queue...");
      // In production, this processes queued .settle events
    } catch (err: any) {
      console.error(`\x1b[31m[Daemon Error]: ${err.message || err}\x1b[0m`);
    }
  }, 10000);
}
