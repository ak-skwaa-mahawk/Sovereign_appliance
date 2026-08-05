import { serve } from "bun";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const MANIFOLD_LEDGER_PATH = join(process.env.HOME || "", "Turbo_Takeoff/public_ledger_wire.jsonl");

serve({
  port: 3000,
  async fetch(req) {
    const url = new URL(req.url);

    // Endpoint: Fetch validated ledger entries for the UI context layer
    if (url.pathname === "/api/ledger/stream" && req.method === "GET") {
      try {
        if (!existsSync(MANIFOLD_LEDGER_PATH)) {
          return new Response(JSON.stringify({ error: "Ledger pipeline offline" }), {
            status: 503,
            headers: { 
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*" 
            }
          });
        }

        // Read the append-only JSONL wire log
        const rawLog = readFileSync(MANIFOLD_LEDGER_PATH, "utf-8");
        const blocks = rawLog
          .trim()
          .split("\n")
          .filter(line => line.length > 0)
          .map(line => JSON.parse(line));

        // Return the full array of cryptographically verified states
        return new Response(JSON.stringify({ success: true, history: blocks }), {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), { 
          status: 500,
          headers: { "Access-Control-Allow-Origin": "*" }
        });
      }
    }

    return new Response("Sovereign Estate API Router Active", { status: 200 });
  },
});

console.log("🚀 [SOVEREIGN ESTATE BACKEND]: Routing data loops on port 3000...");
