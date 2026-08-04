const { PHI } = require('../src/codex_operators');

let E = [0, 1]; // Nothing to first splash

function simulateLayer(n) {
  if (n < 2) return E[n];
  const G_n = Math.pow(n, Math.floor(n/3)); // Scaling per layer group
  const En = E[n-1] + E[n-2] * Math.pow(PHI, -(n-3)) * G_n;
  E.push(En);
  return En;
}

function runSim(maxLayer) {
  for (let i = 2; i <= maxLayer; i++) {
    simulateLayer(i);
  }
  console.log(`Layer \( {maxLayer}: E_ \){maxLayer} ≈ ${E[maxLayer]}`);
}

runSim(89); // Default to Fibonacci threshold