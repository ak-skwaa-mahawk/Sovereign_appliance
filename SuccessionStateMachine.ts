export interface HeirDesignation {
  heirId: string;
  heirPublicKey: string;
  operatingAgreementHash: string;
}

export interface HeartbeatConfig {
  quietTimeoutMs: number; // T_1: Silence duration before QUIET_GRACE (default 30 days)
  gracePeriodMs: number;  // T_2: Duration of QUIET_GRACE before ATTESTATION (default 14 days)
}

export type MachineState = "ACTIVE_FLIGHT" | "QUIET_GRACE" | "ATTESTATION" | "ROTATED_CONTINUITY";

export interface SuccessionRecord {
  state: MachineState;
  lastHeartbeatTimestamp: number;
  primaryKeyId: string;
  heir: HeirDesignation;
  transitionLog: string[];
}

export class SuccessionStateMachine {
  private record: SuccessionRecord;
  private config: HeartbeatConfig;

  constructor(
    primaryKeyId: string,
    heir: HeirDesignation,
    config: HeartbeatConfig = { quietTimeoutMs: 2592000000, gracePeriodMs: 1209600000 }
  ) {
    this.record = {
      state: "ACTIVE_FLIGHT",
      lastHeartbeatTimestamp: Date.now(),
      primaryKeyId,
      heir,
      transitionLog: [`Initialized state machine for Primary: ${primaryKeyId}`],
    };
    this.config = config;
  }

  public registerPulse(callerKeyId: string): boolean {
    if (callerKeyId !== this.record.primaryKeyId) {
      return false;
    }
    this.record.lastHeartbeatTimestamp = Date.now();
    if (this.record.state !== "ACTIVE_FLIGHT") {
      this.record.state = "ACTIVE_FLIGHT";
      this.record.transitionLog.push(
        `[Heartbeat]: Primary re-authenticated. State reset to ACTIVE_FLIGHT at ${new Date().toISOString()}`
      );
    }
    return true;
  }

  public evaluateState(now: number = Date.now()): MachineState {
    const elapsed = now - this.record.lastHeartbeatTimestamp;

    if (elapsed >= this.config.quietTimeoutMs && elapsed < (this.config.quietTimeoutMs + this.config.gracePeriodMs)) {
      if (this.record.state !== "QUIET_GRACE") {
        this.record.state = "QUIET_GRACE";
        this.record.transitionLog.push(
          `[T_1 Breached]: Elapsed ${elapsed}ms. State shifted to QUIET_GRACE.`
        );
      }
    } else if (elapsed >= (this.config.quietTimeoutMs + this.config.gracePeriodMs)) {
      if (this.record.state !== "ATTESTATION" && this.record.state !== "ROTATED_CONTINUITY") {
        this.record.state = "ATTESTATION";
        this.record.transitionLog.push(
          `[T_2 Expired]: Grace period ended. State shifted to ATTESTATION.`
        );
      }
    }

    return this.record.state;
  }

  public executeSuccessionRotation(heirId: string, proofHash: string): boolean {
    if (this.record.state !== "ATTESTATION") {
      return false;
    }

    if (this.record.heir.heirId === heirId) {
      this.record.primaryKeyId = heirId;
      this.record.state = "ROTATED_CONTINUITY";
      this.record.transitionLog.push(
        `[Rotation Complete]: Primary key rotated to Heir (${heirId}) using proof [${proofHash}]`
      );
      return true;
    }

    return false;
  }

  public loadFromRecord(record: SuccessionRecord): void {
    this.record = record;
  }

  public getStatus(): SuccessionRecord {
    return { ...this.record };
  }
}
