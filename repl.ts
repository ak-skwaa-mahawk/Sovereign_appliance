import * as readline from "readline";
import { SovereignEngine } from "./engine";
import { MerkleLedger } from "./MerkleLedger";
import { SepoliaRelayerClient } from "./SepoliaRelayerClient";

class SovereignREPL {
  private engine: SovereignEngine;
  private rl: readline.Interface;

  constructor() {
    this.engine = new SovereignEngine();
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: "\x1b[36msovereign>\x1b[0m ",
    });
  }

  public async start(): Promise<void> {
    console.clear();
    console.log("\x1b[35m=====================================================\x1b[0m");
    console.log("\x1b[1m\x1b[32m       SOVEREIGN ENGINE — INTERACTIVE REPL           \x1b[0m");
    console.log("\x1b[35m=====================================================\x1b[0m");
    console.log(" Commands: \x1b[33m.telemetry\x1b[0m, \x1b[33m.export\x1b[0m, \x1b[33m.settle\x1b[0m (Sepolia bridge), \x1b[33m.clear\x1b[0m, \x1b[33m.exit\x1b[0m\n");

    await this.engine.initialize();

    this.rl.prompt();

    this.rl.on("line", async (line) => {
      let input = line.trim();

      if (!input) {
        this.rl.prompt();
        return;
      }

      if (input.startsWith("sovereign>")) {
        input = input.replace(/^sovereign>\s*/, "").trim();
      }

      if (input === ".exit" || input === "exit") {
        console.log("\n\x1b[33mShutting down Sovereign Engine and flushing ledger...\x1b[0m");
        this.engine.shutdown();
        process.exit(0);
      }

      if (input === ".clear") {
        console.clear();
        this.rl.prompt();
        return;
      }

      if (input === ".export") {
        const continuation = (this.engine as any).continuation;
        const stateExport = continuation.generateExport();
        console.log("\n\x1b[32m--- CRYPTOGRAPHIC MERKLE STATE EXPORT ---\x1b[0m");
        console.log(` Timestamp:    ${new Date(stateExport.exportTimestamp).toISOString()}`);
        console.log(` Merkle Root:  \x1b[33m${stateExport.merkleRoot}\x1b[0m`);
        console.log(` Node Count:   ${stateExport.nodeCount}`);
        console.log(` Master Key:   ${stateExport.masterKeyId}`);
        console.log(` State:        ${stateExport.machineState}`);
        console.log(` Signature:    \x1b[36m${stateExport.signature}\x1b[0m`);

        if (stateExport.nodes.length > 0) {
          const sampleNode = stateExport.nodes[0];
          const proof = MerkleLedger.generateProof(stateExport.nodes, sampleNode.nodeId);
          if (proof) {
            const verified = MerkleLedger.verifyProof(proof);
            console.log(`\n \x1b[34m[Merkle Proof Verification for Node ${sampleNode.nodeId}]:\x1b[0m ${verified ? "\x1b[32mVALID PROOF\x1b[0m" : "\x1b[31mINVALID\x1b[0m"}`);
          }
        }
        console.log("");
        this.rl.prompt();
        return;
      }

      if (input === ".settle") {
        const continuation = (this.engine as any).continuation;
        const relayerClient = new SepoliaRelayerClient(continuation);
        const result = await relayerClient.submitEngineStateToRollup();
        if (result.txHash) {
          this.engine.supervisor.recordSettlementTx(result.txHash);
        }
        this.rl.prompt();
        return;
      }

      if (input === ".telemetry") {
        const health = await this.engine.supervisor.sampleTelemetry();
        console.log("\n\x1b[34m--- REAL-TIME METACOGNITIVE TELEMETRY ---\x1b[0m");
        console.log(` Status:             \x1b[1m${health.status}\x1b[0m`);
        console.log(` Coherence Index (C): \x1b[33m${health.coherenceIndex}\x1b[0m`);
        console.log(` Buffer Margin (B):   \x1b[33m${health.bufferMargin}\x1b[0m`);
        console.log(` Entropy Delta (ΔE):  \x1b[33m${health.entropyDelta}\x1b[0m`);
        console.log(` Master Key ID:      \x1b[32m${health.currentMasterKey}\x1b[0m`);
        console.log(` Succession State:   \x1b[35m${health.machineState}\x1b[0m`);
        console.log(` Last Settled TX:    \x1b[33m${health.lastSettledTxHash}\x1b[0m`);
        console.log(` Shear Energy:       \x1b[36m${health.validationProof.shearEnergy}\x1b[0m`);
        console.log(` Invariant Intact:   \x1b[32m${health.validationProof.invariantIntact}\x1b[0m\n`);
        this.rl.prompt();
        return;
      }

      try {
        await this.engine.runCognitiveCycle(input);
      } catch (err: any) {
        console.log(`\x1b[31m[REPL Exception]: ${err.message}\x1b[0m`);
      }

      console.log("");
      this.rl.prompt();
    });

    this.rl.on("close", () => {
      console.log("\nExiting REPL session.");
      this.engine.shutdown();
      process.exit(0);
    });
  }
}

(async () => {
  const repl = new SovereignREPL();
  await repl.start();
})();
