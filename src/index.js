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

// Probe endpoint
app.post('/aggregate', (req, res) => {
  const probe = echo_system.layer_1_probe(req.body);
  const filtered = echo_system.layer_2_filter(probe);
  const locked = echo_system.layer_3_lock(filtered);
  res.json(locked);
});

// Mesh connection
wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: "vitality_echo", node: NODE }));
});

console.log("COLLECTIVE_COIL_ENGAGED - Awaiting kin");
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
