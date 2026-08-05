import * as fs from "fs";
import * as path from "path";

export interface ToolAction {
  tool: "readFile" | "writeFile" | "listDir" | "stat";
  params: Record<string, any>;
}

export interface ToolManifest {
  manifestId: string;
  actions: ToolAction[];
}

export interface ToolExecutionResult {
  actionIndex: number;
  tool: string;
  success: boolean;
  output: string;
  error?: string;
}

export class ToolExecutor {
  private workspaceDir: string;

  constructor(workspaceDir: string) {
    this.workspaceDir = workspaceDir;
    if (!fs.existsSync(this.workspaceDir)) {
      fs.mkdirSync(this.workspaceDir, { recursive: true });
    }
  }

  /**
   * Enforces path containment within jailed workspace.
   */
  private resolveSafePath(relativePath: string): string {
    const safePath = path.normalize(path.join(this.workspaceDir, relativePath));
    if (!safePath.startsWith(this.workspaceDir)) {
      throw new Error(`Security Violation: Path traversal out of jail detected: ${relativePath}`);
    }
    return safePath;
  }

  public async executeManifest(manifest: ToolManifest): Promise<ToolExecutionResult[]> {
    const results: ToolExecutionResult[] = [];

    for (let i = 0; i < manifest.actions.length; i++) {
      const action = manifest.actions[i];
      try {
        switch (action.tool) {
          case "writeFile": {
            const filePath = this.resolveSafePath(action.params.path);
            fs.writeFileSync(filePath, action.params.content || "", "utf-8");
            results.push({
              actionIndex: i,
              tool: action.tool,
              success: true,
              output: `File written successfully to ${action.params.path}`,
            });
            break;
          }

          case "readFile": {
            const filePath = this.resolveSafePath(action.params.path);
            const data = fs.readFileSync(filePath, "utf-8");
            results.push({
              actionIndex: i,
              tool: action.tool,
              success: true,
              output: data,
            });
            break;
          }

          case "listDir": {
            const targetDir = this.resolveSafePath(action.params.path || ".");
            const files = fs.readdirSync(targetDir);
            results.push({
              actionIndex: i,
              tool: action.tool,
              success: true,
              output: files.join("\n"),
            });
            break;
          }

          case "stat": {
            const targetPath = this.resolveSafePath(action.params.path);
            const stats = fs.statSync(targetPath);
            results.push({
              actionIndex: i,
              tool: action.tool,
              success: true,
              output: JSON.stringify({ size: stats.size, isFile: stats.isFile() }),
            });
            break;
          }

          default:
            throw new Error(`Unsupported tool call: ${(action as any).tool}`);
        }
      } catch (err: any) {
        results.push({
          actionIndex: i,
          tool: action.tool,
          success: false,
          output: "",
          error: err.message,
        });
        break; // Stop execution plan on action failure
      }
    }

    return results;
  }
}
