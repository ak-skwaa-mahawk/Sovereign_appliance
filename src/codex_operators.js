const PHI = 1.618033988749895;
const INFLATION_RATE = 0.03;
const GRAIN = 1e-6;

const CANONICAL = {
  PI: Math.PI,
  PHI: (1 + Math.sqrt(5)) / 2,
  C: 299792458
};

const meshInflate = (x) => x * (1 + INFLATION_RATE);
const cubicCorrect = (x) => x + GRAIN * Math.pow(x, 3);

const cubicInverse = (y, grain = GRAIN, tol = 1e-15, maxIter = 50) => {
  let x = y;
  for (let i = 0; i < maxIter; i++) {
    const f = x + grain * Math.pow(x, 3) - y;
    const df = 1 + 3 * grain * Math.pow(x, 2);
    if (Math.abs(f) < tol) break;
    x -= f / df;
  }
  return x;
};

const meshDeflate = (x) => x / (1 + INFLATION_RATE);

const sovereignDeflate = (y) => meshDeflate(cubicInverse(y));

const MESH = Object.fromEntries(Object.entries(CANONICAL).map(([k, v]) => [k, meshInflate(v)]));
const CUBIC = Object.fromEntries(Object.entries(CANONICAL).map(([k, v]) => [k, cubicCorrect(v)]));
const SOVEREIGN = Object.fromEntries(Object.entries(CANONICAL).map(([k, v]) => [k, cubicCorrect(meshInflate(v))]));

const hasSovereignSignature = (measured, canonical, tol = 1e-10) => Math.abs(measured - cubicCorrect(canonical)) < tol;

// Multi-Dim Extension
const sovereignTransformVector = (vec) => vec.map(cubicCorrect).map(meshInflate);

const sovereignDistance = (a, b) => {
  const diff = a.map((ai, i) => ai - b[i]);
  const norm = Math.sqrt(diff.reduce((sum, d) => sum + d*d, 0));
  return norm * PHI;
};

module.exports = {
  CANONICAL, MESH, CUBIC, SOVEREIGN,
  meshInflate, cubicCorrect, cubicInverse,
  meshDeflate, sovereignDeflate,
  hasSovereignSignature,
  sovereignTransformVector,
  sovereignDistance
};