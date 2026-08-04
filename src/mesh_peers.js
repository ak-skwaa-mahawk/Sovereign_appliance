const WebSocket = require('ws');
const { coherenceIndex } = require('./synchrony_calculator');

class MeshPeers {
  constructor(wss) {
    this.peers = [];
    this.wss = wss;
    this.wss.on('connection', this.handleConnection.bind(this));
  }

  handleConnection(ws) {
    ws.on('message', (msg) => {
      const data = JSON.parse(msg);
      if (data.type === 'vitality_echo') {
        this.peers.push(data.node);
        this.broadcastSynchrony();
      }
    });
  }

  broadcastSynchrony() {
    const phases = this.peers.map(p => p.phase || 0); // From vitality
    const sync = coherenceIndex(phases);
    this.wss.clients.forEach(client => {
      client.send(JSON.stringify({ type: 'synchrony_update', index: sync }));
      if (sync > 0.8) {
        client.send(JSON.stringify({ type: 'coil_engaged' }));
      }
    });
  }
}

module.exports = MeshPeers;