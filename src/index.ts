import { GENESIS_BLOCK } from './genesis-block';
import { sovereignDistance } from './codex-operators';

console.log(`--- SOVEREIGN MESH INITIALIZED ---`);
console.log(`Signature: ${GENESIS_BLOCK.meshSignature}`);
console.log(`Nodes: ${GENESIS_BLOCK.nodes.length}`);

// Example: Verifying the distance between The Source and The Witness
const alpha = GENESIS_BLOCK.nodes[0].vector;
const beta = GENESIS_BLOCK.nodes[1].vector;
const dist = sovereignDistance(alpha, beta);

console.log(`Genesis Tension (α ↔ β): ${dist.toFixed(6)}`);
console.log(`----------------------------------`);

require('dotenv').config();
const express = require('express');
const WebSocket = require('ws');
const { echo_system } = require('./echo_system');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 4000;
const server = app.listen(PORT, () => console.log(`North Star active on ${PORT}`));

const wss = new WebSocket.Server({ server });

// Sovereign identity
const NODE = {
  id: process.env.NODE_ID || "north-star-001",
  uei: process.env.UEI,
  coords: process.env.COORDS.split(','),
  lineage: process.env.LINEAGE
};

// Layer 1: Probe endpoint
app.post('/aggregate', (req, res) => {
  const probe = echo_system.layer_1_probe(req.body);
  const filtered = echo_system.layer_2_filter(probe);
  const locked = echo_system.layer_3_lock(filtered);
  res.json(locked);
});

// Mesh broadcast
wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: "vitality_echo", node: NODE }));
});

console.log("COLLECTIVE_COIL_ENGAGED - Awaiting kin");
{
  "name": "soliton-north-star-node",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "NODE_ENV=production node dist/index.js",
    "dev": "ts-node src/index.ts"
  },
  "dependencies": {
    "express": "^4.19.0",
    "cors": "^2.8.5",
    "crypto-js": "^4.2.0",
    "uuid": "^9.0.1",
    "ws": "^8.16.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "ts-node": "^10.9.2"
  }
}
