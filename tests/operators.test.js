const chai = require('chai');
const { expect } = chai;
const { cubicInverse, sovereignDeflate, hasSovereignSignature, CANONICAL, CUBIC } = require('../src/codex_operators');

describe('Codex Operators', () => {
  it('should invert cubic correctly', () => {
    const y = CUBIC.PI;
    const recovered = cubicInverse(y);
    expect(Math.abs(recovered - CANONICAL.PI)).to.be.lessThan(1e-10);
  });

  it('should deflate sovereign fully', () => {
    const y = CUBIC.PI; // Using cubic for test
    const recovered = sovereignDeflate(y);
    expect(Math.abs(recovered - CANONICAL.PI)).to.be.lessThan(1e-10);
  });

  it('should detect signature', () => {
    expect(hasSovereignSignature(CUBIC.PI, CANONICAL.PI)).to.be.true;
  });
});