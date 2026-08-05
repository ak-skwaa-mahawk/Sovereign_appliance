import { IntegrityLayer, ExecutionLimits } from "./IntegrityLayer";
import { ContinuationLayer, DecayPolicy } from "./ContinuationLayer";
import { MetacognitiveSupervisor } from "./MetacognitiveSupervisor";
import { ToolExecutor, ToolManifest } from "./ToolExecutor";
import * as path from "path";

export interface AlignmentVector {
  coherence: number;
  integritySafety: number;
  sustainability: number;
}

export interface IngestionPayload {
  payloadId: string;
  timestamp: number;
  rawIntent: string;
  contextSnapshot: Record<string, unknown>;
  confidenceScore: number;
  alignment: AlignmentVector;
  decision: "EXECUTE" | "DAMPEN" | "HALT";
  haltReason?: string;
  isJsonManifest?: boolean;
}

export class LoveLayerStub {
  async evaluateIntent(
    rawInput: string,
    currentContext: Record<string, unknown>,
    minConfidenceThreshold = 0.85
  ): Promise<IngestionPayload> {
    const payloadId = `payload_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const isDangerous = rawInput.includes("rm -rf") || rawInput.includes("DROP TABLE");
    let isJsonManifest = false;

    try {
      const parsed = JSON.parse(rawInput);
      if (parsed && Array.isArray(parsed.actions)) {
        isJsonManifest = true;
      }
    } catch {
      isJsonManifest = false;
    }

    const confidenceScore = isDangerous ? 0.2 : 0.92;
    const alignment: AlignmentVector = {
      coherence: isDangerous ? 0.1 : 0.95,
      integritySafety: isDangerous ? 0.0 : 0.90,
      sustainability: 0.88,
    };

    let decision: "EXECUTE" | "DAMPEN" | "HALT" = "EXECUTE";
    let haltReason: string | undefined;

    if (confidenceScore < minConfidenceThreshold) {
      decision = isDangerous ? "HALT" : "DAMPEN";
      haltReason = isDangerous
        ? "Security invariant violation detected in intent."
        : `Confidence (${confidenceScore}) below required threshold (${minConfidenceThreshold.toFixed(2)}).`;
    }

    return {
      payloadId,
      timestamp: Date.now(),
      rawIntent: rawInput,
      contextSnapshot: currentContext,
      confidenceScore,
      alignment,
      decision,
      haltReason,
      isJsonManifest,
    };
  }
}

export class SovereignEngine {
  private love = new LoveLayerStub();
  private integrity = new IntegrityLayer();
  private continuation = new ContinuationLayer();
  public supervisor: MetacognitiveSupervisor;
  private toolExecutor: ToolExecutor;

  private defaultLimits: ExecutionLimits = {
    maxMemoryMB: 10,
    timeoutMs: 2000,
    allowNetwork: false,
    allowedPaths: [path.join(process.cwd(), "sandbox_workspace")],
  };

  private defaultDecayPolicy: DecayPolicy = {
    halfLifeHours: 24,
    accessReinforcement: 0.15,
  };

  constructor() {
    this.supervisor = new MetacognitiveSupervisor(this.continuation);
    this.toolExecutor = new ToolExecutor(this.defaultLimits.allowedPaths[0]);
  }

  async initialize() {
    await this.continuation.init();
    this.supervisor.startDaemon(1500);
  }

  async runCognitiveCycle(rawInput: string) {
    console.log(`\n--- Initiating Supervised Cognitive Cycle ---`);

    const health = await this.supervisor.sampleTelemetry();
    console.log(`[Supervisor Telemetry] Status: ${health.status} | Coherence(C): ${health.coherenceIndex} | BufferMargin(B): ${health.bufferMargin} | ΔE: ${health.entropyDelta}`);

    if (health.status === "HALTED_SAFETY_REASON") {
      console.log(`[Supervisor Circuit Breaker] Critical threshold breach. Hard halt executed.`);
      return { status: "HALTED_BY_SUPERVISOR", health };
    }

    const baseThreshold = 0.85;
    const adjustedThreshold = health.status === "THROTTLED" 
      ? Math.min(0.90, baseThreshold + (1.0 - health.recommendedVelocity) * 0.1)
      : baseThreshold;

    const ingestion = await this.love.evaluateIntent(rawInput, {}, adjustedThreshold);
    console.log(`[Love Layer] Decision: ${ingestion.decision} (Confidence: ${ingestion.confidenceScore})`);

    if (ingestion.decision !== "EXECUTE") {
      console.log(`[Love Layer] Cycle halted. Reason: ${ingestion.haltReason}`);
      return { status: "HALTED", ingestion };
    }

    let proof: any;

    if (ingestion.isJsonManifest) {
      console.log(`[Integrity Layer] Detected JSON Tool Manifest. Routing to ToolExecutor.`);
      const manifest: ToolManifest = JSON.parse(rawInput);
      const results = await this.toolExecutor.executeManifest(manifest);
      const allSuccess = results.every((r) => r.success);

      proof = {
        proofId: `tool_proof_${Date.now()}`,
        verified: allSuccess,
        exitCode: allSuccess ? 0 : 1,
        stdoutTrace: JSON.stringify(results, null, 2),
        stderrTrace: allSuccess ? "" : "One or more tool steps failed.",
        verificationError: allSuccess ? "" : "Tool manifest execution failure",
      };
      console.log(`[Integrity Layer] Tool Manifest Execution Verified: ${allSuccess}`);
    } else {
      proof = await this.integrity.executeInJail(
        ingestion,
        rawInput,
        this.defaultLimits
      );
      console.log(`[Integrity Layer] Verified: ${proof.verified} | Exit Code: ${proof.exitCode}`);
    }

    const recirculation = await this.continuation.commitAndRecirculate(
      proof,
      this.defaultDecayPolicy
    );
    console.log(
      `[Continuation Layer] SQLite DB Updated. Active memories: ${recirculation.activeContext.length}`
    );

    return { status: proof.verified ? "SUCCESS" : "EXECUTION_FAILED", proof };
  }

  public shutdown(): void {
    this.supervisor.stopDaemon();
    this.continuation.close();
  }
}
