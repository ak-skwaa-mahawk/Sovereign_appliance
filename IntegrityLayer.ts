import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";

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
}

export interface ExecutionLimits {
  maxMemoryMB: number;
  timeoutMs: number;
  allowNetwork: boolean;
  allowedPaths: string[];
}

export interface ExecutionProof {
  proofId: string;
  payloadId: string;
  exitCode: number;
  stdoutTrace: string;
  stderrTrace: string;
  resourceUsage: {
    peakMemoryMB: number;
    cpuTimeMs: number;
  };
  verified: boolean;
  verificationError?: string;
}

export class IntegrityLayer {
  async executeInJail(
    payload: IngestionPayload,
    command: string,
    limits: ExecutionLimits
  ): Promise<ExecutionProof> {
    const proofId = `proof_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const startTime = Date.now();

    // Use local Termux directory instead of root /tmp
    const fallbackPath = path.join(process.cwd(), "sandbox_workspace");
    const primaryJailPath = limits.allowedPaths[0] || fallbackPath;
    const resolvedJail = path.resolve(primaryJailPath);

    if (!fs.existsSync(resolvedJail)) {
      fs.mkdirSync(resolvedJail, { recursive: true });
    }

    const hasPathTraversal = limits.allowedPaths.some((p) => {
      const resolved = path.resolve(p);
      return resolved === "/" || p.includes("..");
    });

    if (hasPathTraversal) {
      return {
        proofId,
        payloadId: payload.payloadId,
        exitCode: 1,
        stdoutTrace: "",
        stderrTrace: "PermissionDenied: Jail path attempted root or parent traversal.",
        resourceUsage: { peakMemoryMB: 0, cpuTimeMs: 0 },
        verified: false,
        verificationError: "Filesystem boundary breach prevented.",
      };
    }

    return new Promise<ExecutionProof>((resolve) => {
      let stdoutData = "";
      let stderrData = "";
      let isTimedOut = false;

      const child = spawn("sh", ["-c", command], {
        cwd: resolvedJail,
        env: {
          ...process.env,
          PATH: process.env.PATH,
          TMPDIR: resolvedJail,
        },
      });

      child.stdout.on("data", (chunk) => {
        stdoutData += chunk.toString();
      });

      child.stderr.on("data", (chunk) => {
        stderrData += chunk.toString();
      });

      const timer = setTimeout(() => {
        isTimedOut = true;
        child.kill("SIGKILL");
      }, limits.timeoutMs);

      child.on("close", (code) => {
        clearTimeout(timer);
        const elapsedTime = Date.now() - startTime;
        const exitCode = isTimedOut ? 124 : code ?? 1;

        if (isTimedOut) {
          stderrData += `\n[Integrity Error]: Process killed by Reaper after exceeding timeout of ${limits.timeoutMs}ms.`;
        }

        const memoryUsedMB = process.memoryUsage().heapUsed / (1024 * 1024);
        const verified = exitCode === 0 && !isTimedOut;
        let verificationError: string | undefined;

        if (!verified) {
          verificationError = isTimedOut
            ? `Execution timed out (${limits.timeoutMs}ms)`
            : `Subprocess exited with non-zero status code: ${exitCode}`;
        }

        resolve({
          proofId,
          payloadId: payload.payloadId,
          exitCode,
          stdoutTrace: stdoutData.trim(),
          stderrTrace: stderrData.trim(),
          resourceUsage: {
            peakMemoryMB: parseFloat(memoryUsedMB.toFixed(2)),
            cpuTimeMs: elapsedTime,
          },
          verified,
          verificationError,
        });
      });

      child.on("error", (err) => {
        clearTimeout(timer);
        resolve({
          proofId,
          payloadId: payload.payloadId,
          exitCode: 1,
          stdoutTrace: stdoutData.trim(),
          stderrTrace: err.message,
          resourceUsage: {
            peakMemoryMB: 0,
            cpuTimeMs: Date.now() - startTime,
          },
          verified: false,
          verificationError: `Process failed to spawn: ${err.message}`,
        });
      });
    });
  }
}
