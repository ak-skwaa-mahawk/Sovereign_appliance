import * as crypto from "crypto";
import { MemoryNode } from "./ContinuationLayer";

export interface MerkleProofStep {
  position: "left" | "right";
  hash: string;
}

export interface MerkleProof {
  nodeId: string;
  leafHash: string;
  rootHash: string;
  proof: MerkleProofStep[];
}

export interface StateExportPayload {
  exportTimestamp: number;
  merkleRoot: string;
  nodeCount: number;
  masterKeyId: string;
  machineState: string;
  nodes: MemoryNode[];
  signature: string;
}

export class MerkleLedger {
  /**
   * Computes SHA-256 hash of a memory node
   */
  public static hashNode(node: MemoryNode): string {
    const data = `${node.nodeId}:${node.proofId}:${node.timestamp}:${node.summary}:${node.decayWeight}`;
    return crypto.createHash("sha256").update(data).digest("hex");
  }

  /**
   * Builds Merkle Root from an array of MemoryNodes
   */
  public static buildTree(nodes: MemoryNode[]): { root: string; layers: string[][] } {
    if (nodes.length === 0) {
      const emptyHash = crypto.createHash("sha256").update("EMPTY_LEDGER").digest("hex");
      return { root: emptyHash, layers: [[emptyHash]] };
    }

    let currentLayer = nodes.map((n) => this.hashNode(n));
    const layers: string[][] = [currentLayer];

    while (currentLayer.length > 1) {
      const nextLayer: string[] = [];
      for (let i = 0; i < currentLayer.length; i += 2) {
        if (i + 1 < currentLayer.length) {
          const combined = currentLayer[i] + currentLayer[i + 1];
          nextLayer.push(crypto.createHash("sha256").update(combined).digest("hex"));
        } else {
          // Odd node out: duplicate hash to maintain tree balance
          const combined = currentLayer[i] + currentLayer[i];
          nextLayer.push(crypto.createHash("sha256").update(combined).digest("hex"));
        }
      }
      layers.push(nextLayer);
      currentLayer = nextLayer;
    }

    return { root: currentLayer[0], layers };
  }

  /**
   * Generates an inclusion proof for a given nodeId
   */
  public static generateProof(nodes: MemoryNode[], targetNodeId: string): MerkleProof | null {
    const targetIndex = nodes.findIndex((n) => n.nodeId === targetNodeId);
    if (targetIndex === -1) return null;

    const { root, layers } = this.buildTree(nodes);
    const proofSteps: MerkleProofStep[] = [];
    let idx = targetIndex;

    for (let i = 0; i < layers.length - 1; i++) {
      const layer = layers[i];
      const isRightNode = idx % 2 === 1;
      const pairIndex = isRightNode ? idx - 1 : idx + 1;

      if (pairIndex < layer.length) {
        proofSteps.push({
          position: isRightNode ? "left" : "right",
          hash: layer[pairIndex],
        });
      } else {
        proofSteps.push({
          position: "right",
          hash: layer[idx],
        });
      }

      idx = Math.floor(idx / 2);
    }

    return {
      nodeId: targetNodeId,
      leafHash: this.hashNode(nodes[targetIndex]),
      rootHash: root,
      proof: proofSteps,
    };
  }

  /**
   * Verifies a Merkle Inclusion Proof out-of-band
   */
  public static verifyProof(proof: MerkleProof): boolean {
    let currentHash = proof.leafHash;

    for (const step of proof.proof) {
      const combined = step.position === "left" ? step.hash + currentHash : currentHash + step.hash;
      currentHash = crypto.createHash("sha256").update(combined).digest("hex");
    }

    return currentHash === proof.rootHash;
  }
}
