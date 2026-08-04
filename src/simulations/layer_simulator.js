const { PHI } = require('../src/codex_operators');

let E = [0, 1]; // E0 = nothing, E1 = first splash

function simulateLayer(n) {
  if (n < 2) return E[n];
  let En = E[n-1] + E[n-2] * Math.pow(PHI, -(n-3));
  E.push(En);
  return En;
}

function runSim(maxLayer = 100) {
  for (let i = 2; i <= maxLayer; i++) {
    simulateLayer(i);
  }
  console.log(`Layer \( {maxLayer}: E_ \){maxLayer} ≈ ${E[maxLayer]}`);
  console.log("Converging to φ attractor...");
}

runSim(89); // Your Fibonacci threshold