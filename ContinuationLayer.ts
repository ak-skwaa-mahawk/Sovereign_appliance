import initSqlJs, { Database } from "sql.js";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";
import { SuccessionStateMachine, SuccessionRecord, HeirDesignation } from "./SuccessionStateMachine";
import { MerkleLedger, StateExportPayload } from "./MerkleLedger";

export interface DecayPolicy {
  halfLifeHours: number;
  accessReinforcement: number;
}

export interface MemoryNode {
  nodeId: string;
  proofId: string;
  timestamp: number;
  summary: string;
  decayWeight: number;
  isNegativeExample: boolean;
}

export interface RecirculationState {
  cycleId: string;
  activeContext: MemoryNode[];
  scrubbedCount: number;
  successionState: SuccessionRecord;
  merkleRoot: string;
  reinjectionVector: Record<string, unknown>;
}

export class ContinuationLayer {
  private dbPath: string;
  private db: Database | null = null;
  public successionMachine: SuccessionStateMachine;

  constructor(dbPath?: string) {
    this.dbPath = dbPath || path.join(process.cwd(), "sovereign_ledger.db");
    
    const defaultHeir: HeirDesignation = {
      heirId: "heir_001_sovereign",
      heirPublicKey: "pubkey_heir_sha256_0x99812",
      operatingAgreementHash: "hash_llc_operating_agreement_v1",
    };

    this.successionMachine = new SuccessionStateMachine("primary_sovereign_id", defaultHeir, {
      quietTimeoutMs: 5000,
      gracePeriodMs: 5000,
    });
  }

  public async init(): Promise<void> {
    const SQL = await initSqlJs();

    if (fs.existsSync(this.dbPath)) {
      const filebuffer = fs.readFileSync(this.dbPath);
      this.db = new SQL.Database(filebuffer);
    } else {
      this.db = new SQL.Database();
    }

    this.initializeTables();
    this.loadSuccessionState();
  }

  private initializeTables(): void {
    if (!this.db) return;

    this.db.run(`
      CREATE TABLE IF NOT EXISTS memory_nodes (
        node_id TEXT PRIMARY KEY,
        proof_id TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        summary TEXT NOT NULL,
        decay_weight REAL NOT NULL,
        is_negative_example INTEGER NOT NULL
      );
    `);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS succession_ledger (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        state_json TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      );
    `);

    this.saveToDisk();
  }

  private loadSuccessionState(): void {
    if (!this.db) return;
    const res = this.db.exec("SELECT state_json FROM succession_ledger WHERE id = 1");
    if (res.length > 0 && res[0].values.length > 0) {
      const record = JSON.parse(String(res[0].values[0][0])) as SuccessionRecord;
      this.successionMachine.loadFromRecord(record);
    } else {
      this.persistSuccessionState();
    }
  }

  public persistSuccessionState(): void {
    if (!this.db) return;
    const status = this.successionMachine.getStatus();
    const jsonStr = JSON.stringify(status);
    const now = Date.now();

    this.db.run(
      `INSERT INTO succession_ledger (id, state_json, updated_at) 
       VALUES (1, ?, ?) 
       ON CONFLICT(id) DO UPDATE SET state_json = ?, updated_at = ?`,
      [jsonStr, now, jsonStr, now]
    );

    this.saveToDisk();
  }

  public getActiveNodes(): MemoryNode[] {
    if (!this.db) return [];
    const res = this.db.exec(
      `SELECT node_id, proof_id, timestamp, summary, decay_weight, is_negative_example 
       FROM memory_nodes 
       ORDER BY decay_weight DESC LIMIT 10`
    );

    const activeNodes: MemoryNode[] = [];
    if (res.length > 0 && res[0].values) {
      for (const row of res[0].values) {
        activeNodes.push({
          nodeId: String(row[0]),
          proofId: String(row[1]),
          timestamp: Number(row[2]),
          summary: String(row[3]),
          decayWeight: Number(row[4]),
          isNegativeExample: Number(row[5]) === 1,
        });
      }
    }
    return activeNodes;
  }

  public async commitAndRecirculate(
    proof: any,
    policy: DecayPolicy,
    callerKeyId: string = "primary_sovereign_id"
  ): Promise<RecirculationState> {
    if (!this.db) await this.init();
    if (!this.db) throw new Error("Database failed to initialize.");

    const cycleId = `cycle_${Date.now()}`;
    const nodeId = `mem_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const now = Date.now();

    this.successionMachine.registerPulse(callerKeyId);
    this.successionMachine.evaluateState(now);

    const summary = proof.verified
      ? proof.stdoutTrace || "Executed cleanly"
      : `FAILURE: ${proof.verificationError || proof.stderrTrace}`;

    this.db.run(
      `INSERT INTO memory_nodes (node_id, proof_id, timestamp, summary, decay_weight, is_negative_example)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [nodeId, proof.proofId, now, summary, proof.verified ? 1.0 : 0.6, proof.verified ? 0 : 1]
    );

    const lambda = Math.LN2 / policy.halfLifeHours;
    const stmt = this.db.prepare("SELECT node_id, timestamp, decay_weight FROM memory_nodes");
    while (stmt.step()) {
      const row = stmt.getAsObject();
      const elapsedHours = (now - Number(row.timestamp)) / 3600000.0;
      const newWeight = Number(row.decay_weight) * Math.exp(-lambda * elapsedHours);
      this.db.run("UPDATE memory_nodes SET decay_weight = ? WHERE node_id = ?", [newWeight, row.node_id]);
    }
    stmt.free();

    this.db.run("DELETE FROM memory_nodes WHERE decay_weight <= 0.2");

    const activeNodes = this.getActiveNodes();
    const { root: merkleRoot } = MerkleLedger.buildTree(activeNodes);

    this.persistSuccessionState();

    return {
      cycleId,
      activeContext: activeNodes,
      scrubbedCount: 0,
      successionState: this.successionMachine.getStatus(),
      merkleRoot,
      reinjectionVector: {
        latestProofId: proof.proofId,
        lastExecutionVerified: proof.verified,
        activeMemoryCount: activeNodes.length,
        currentMasterKey: this.successionMachine.getStatus().primaryKeyId,
        machineState: this.successionMachine.getStatus().state,
      },
    };
  }

  public generateExport(): StateExportPayload {
    const activeNodes = this.getActiveNodes();
    const { root: merkleRoot } = MerkleLedger.buildTree(activeNodes);
    const successionStatus = this.successionMachine.getStatus();
    const timestamp = Date.now();

    const exportData = `${timestamp}:${merkleRoot}:${activeNodes.length}:${successionStatus.primaryKeyId}:${successionStatus.state}`;
    const signature = crypto.createHash("sha256").update(exportData).digest("hex");

    return {
      exportTimestamp: timestamp,
      merkleRoot,
      nodeCount: activeNodes.length,
      masterKeyId: successionStatus.primaryKeyId,
      machineState: successionStatus.state,
      nodes: activeNodes,
      signature,
    };
  }

  private saveToDisk(): void {
    if (!this.db) return;
    const data = this.db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(this.dbPath, buffer);
  }

  public close(): void {
    if (this.db) {
      this.persistSuccessionState();
      this.db.close();
    }
  }
}
