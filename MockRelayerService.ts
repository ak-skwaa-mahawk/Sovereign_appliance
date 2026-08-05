import * as http from "http";

const PORT = 3098;

const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url === "/v1/batch") {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk.toString();
    });

    req.on("end", () => {
      try {
        const payload = JSON.parse(body);
        console.log(`\n\x1b[32m[Relayer Daemon]: Ingested Batch Payload!\x1b[0m`);
        console.log(` Chain ID:      ${payload.chainId}`);
        console.log(` Target:        ${payload.contractAddress}`);
        console.log(` Engine Root:   ${payload.commitment?.engineStateRoot}`);
        console.log(` Domain Leaf:   ${payload.commitment?.leafHash}`);

        // Generate a pseudo-txHash representing Sepolia submission
        const txHash = "0x" + require("crypto")
          .createHash("sha256")
          .update(payload.commitment?.leafHash + Date.now().toString())
          .digest("hex");

        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            status: "SUCCESS",
            txHash: txHash,
            blockNumber: 6128495,
            message: "Batch successfully posted to DA and Sepolia state anchor.",
          })
        );
      } catch (err: any) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
  } else {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found");
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`\x1b[36m[Relayer Daemon]: Listening on http://127.0.0.1:${PORT}/v1/batch...\x1b[0m`);
});
