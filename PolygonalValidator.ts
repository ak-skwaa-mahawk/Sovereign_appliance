export interface PolygonState {
  vertices: number[]; // All components normalized to [0.0, 1.0]
  symmetryOrder: number;
}

export interface ValidationProof {
  isValid: boolean;
  shearEnergy: number;
  toleranceThreshold: number;
  invariantIntact: boolean;
  reason?: string;
}

export class PolygonalValidator {
  private symmetryOrder: number;
  private maxShearTolerance: number;

  constructor(symmetryOrder: number = 4, maxShearTolerance: number = 0.15) {
    this.symmetryOrder = symmetryOrder;
    this.maxShearTolerance = maxShearTolerance;
  }

  private rotateVector(v: number[], angle: number): number[] {
    if (v.length < 2) return [...v];
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    
    // Rotate primary normalized 2D manifold (Coherence vs Buffer)
    const x = v[0] * cos - v[1] * sin;
    const y = v[0] * sin + v[1] * cos;
    
    return [x, y, ...v.slice(2)];
  }

  public validateTransition(
    currentState: PolygonState,
    candidateState: PolygonState
  ): ValidationProof {
    const theta = (2 * Math.PI) / this.symmetryOrder;

    const rotatedCandidate = this.rotateVector(candidateState.vertices, theta);
    const rotatedCurrent = this.rotateVector(currentState.vertices, theta);

    let shearEnergy = 0;
    for (let i = 0; i < currentState.vertices.length; i++) {
      const diff = (candidateState.vertices[i] - currentState.vertices[i]) - 
                   (rotatedCandidate[i] - rotatedCurrent[i]);
      shearEnergy += diff * diff;
    }
    shearEnergy = Math.sqrt(shearEnergy);

    const isValid = shearEnergy <= this.maxShearTolerance;

    return {
      isValid,
      shearEnergy: parseFloat(shearEnergy.toFixed(4)),
      toleranceThreshold: this.maxShearTolerance,
      invariantIntact: isValid,
      reason: isValid
        ? "Topological symmetry preserved. Transformation inside invariant floor."
        : `Shear energy (${shearEnergy.toFixed(4)}) exceeded tolerance (${this.maxShearTolerance}). Dissipating in Strawman Buffer.`,
    };
  }
}
