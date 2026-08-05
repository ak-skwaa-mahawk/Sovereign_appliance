import { ContinuationLayer } from "./ContinuationLayer";
import { PolygonalValidator, PolygonState, ValidationProof } from "./PolygonalValidator";

export interface SystemHealthMetrics {
  coherenceIndex: number;
  bufferMargin: number;
  entropyDelta: number;
  status: "OPTIMAL" | "THROTTLED" | "HALTED_SAFETY_REASON";
  recommendedVelocity: number;
  currentMasterKey: string;
  machineState: string;
  lastSettledTxHash?: string;
  validationProof: ValidationProof;
}

export class MetacognitiveSupervisor {
  private continuation: ContinuationLayer;
  private validator: PolygonalValidator;
  private monitorInterval: NodeJS.Timeout | null = null;
  private lastPolygonState: PolygonState | null = null;
  private lastSettledTxHash: string = "0x0000000000000000000000000000000000000000000000000000000000000000";

  private currentHealth: SystemHealthMetrics = {
    coherenceIndex: 1.0,
    bufferMargin: 1.0,
    entropyDelta: 0,
    status: "OPTIMAL",
    recommendedVelocity: 1.0,
    currentMasterKey: "primary_sovereign_id",
    machineState: "ACTIVE_FLIGHT",
    lastSettledTxHash: this.lastSettledTxHash,
    validationProof: {
      isValid: true,
      shearEnergy: 0.0,
      toleranceThreshold: 0.15,
      invariantIntact: true,
      reason: "Initial state",
    },
  };

  constructor(continuation: ContinuationLayer) {
    this.continuation = continuation;
    this.validator = new PolygonalValidator(4, 0.15);
  }

  public recordSettlementTx(txHash: string): void {
    this.lastSettledTxHash = txHash;
  }

  public startDaemon(intervalMs: number = 1500): void {
    if (this.monitorInterval) return;

    this.monitorInterval = setInterval(async () => {
      await this.sampleTelemetry();
    }, intervalMs);
  }

  public async sampleTelemetry(): Promise<SystemHealthMetrics> {
    const memUsage = process.memoryUsage();
    const heapLimit = 50 * 1024 * 1024;
    const bufferMargin = Math.max(0, 1 - memUsage.heapUsed / heapLimit);

    const recentState = await this.continuation.commitAndRecirculate(
      {
        proofId: `telemetry_${Date.now()}`,
        verified: true,
        stdoutTrace: "SUPERVISOR_PING",
        verificationError: "",
      },
      { halfLifeHours: 24, accessReinforcement: 0.1 }
    );

    const activeNodes = recentState.activeContext;
    const totalCount = activeNodes.length;
    const negativeCount = activeNodes.filter((n) => n.isNegativeExample).length;

    const coherenceIndex = totalCount > 0 ? (totalCount - negativeCount) / totalCount : 1.0;
    const entropyDelta = totalCount - recentState.scrubbedCount;

    const normalizedEntropy = Math.min(1.0, Math.max(0.0, entropyDelta / 10.0));

    const candidatePolygon: PolygonState = {
      vertices: [coherenceIndex, bufferMargin, normalizedEntropy, 0.92],
      symmetryOrder: 4,
    };

    if (!this.lastPolygonState) {
      this.lastPolygonState = candidatePolygon;
    }

    const proof = this.validator.validateTransition(this.lastPolygonState, candidatePolygon);
    this.lastPolygonState = candidatePolygon;

    let status: "OPTIMAL" | "THROTTLED" | "HALTED_SAFETY_REASON" = "OPTIMAL";
    let recommendedVelocity = 1.0;

    if (!proof.isValid || bufferMargin < 0.15 || coherenceIndex < 0.5) {
      status = "HALTED_SAFETY_REASON";
      recommendedVelocity = 0.0;
    } else if (bufferMargin < 0.35 || coherenceIndex < 0.75) {
      status = "THROTTLED";
      recommendedVelocity = 0.5;
    }

    const successionStatus = this.continuation.successionMachine.getStatus();

    this.currentHealth = {
      coherenceIndex: parseFloat(coherenceIndex.toFixed(2)),
      bufferMargin: parseFloat(bufferMargin.toFixed(2)),
      entropyDelta,
      status,
      recommendedVelocity,
      currentMasterKey: successionStatus.primaryKeyId,
      machineState: successionStatus.state,
      lastSettledTxHash: this.lastSettledTxHash,
      validationProof: proof,
    };

    return this.currentHealth;
  }

  public getHealth(): SystemHealthMetrics {
    return this.currentHealth;
  }

  public stopDaemon(): void {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
    }
  }
}
