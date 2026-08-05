import * as crypto from "crypto";
import { StateExportPayload } from "./MerkleLedger";

export interface OnChainEngineBatch {
  batchId: string;
  timestamp: number;
  engineMerkleRoot: string;
  masterKeyId: string;
  machineState: string;
  nodeCount: number;
  domainSeparatedLeaf: string;
  localSignature: string;
}

export class EngineRollupBridge {
  private chainId: number;
  private rollupContractAddress: string;

  constructor(chainId: number = 11155111, rollupContractAddress: string = "0x0000000000000000000000000000000000000000") {
    this.chainId = chainId;
    this.rollupContractAddress = rollupContractAddress;
  }

  /**
   * Computes a keccak-style domain-separated leaf for inclusion in the rollup DA blob
   */
  public computeDomainSeparatedLeaf(payload: StateExportPayload): string {
    const domainHeader = `SOVEREIGN_ENGINE_v1:CHAIN_${this.chainId}:CONTRACT_${this.rollupContractAddress}`;
    const rawLeaf = `${domainHeader}:${payload.exportTimestamp}:${payload.merkleRoot}:${payload.masterKeyId}:${payload.machineState}:${payload.nodeCount}`;
    return crypto.createHash("sha256").update(rawLeaf).digest("hex");
  }

  /**
   * Transforms local export into an L2/Sepolia Rollup Batch Payload
   */
  public prepareBatchPayload(payload: StateExportPayload): OnChainEngineBatch {
    const leaf = this.computeDomainSeparatedLeaf(payload);
    const batchId = `batch_sepolia_${payload.exportTimestamp}_${leaf.substring(0, 8)}`;

    return {
      batchId,
      timestamp: payload.exportTimestamp,
      engineMerkleRoot: payload.merkleRoot,
      masterKeyId: payload.masterKeyId,
      machineState: payload.machineState,
      nodeCount: payload.nodeCount,
      domainSeparatedLeaf: leaf,
      localSignature: payload.signature,
    };
  }
}
