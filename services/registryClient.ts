const NORTH_STAR_WS = "wss://northstar.soliton.registry:4001";

async function bootstrapPeers() {
  // Fetch seeds
  const seedsRes = await fetch("https://northstar.soliton.registry/.well-known/soliton-seeds.json");
  const seeds = await seedsRes.json();

  seeds.nodes.forEach(node => {
    if (!currentPeers.includes(node.ws)) {
      addPeer(node.ws);
    }
  });
}

// Call on app start
bootstrapPeers();
