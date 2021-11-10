export interface LabelerEvaluativeStats {
  labeler: string,
  coverage: number,
  conflicts: number,
  polarity: Array<number>,
  experimental_accuracy?: number,
  empirical_accuracy?: number,
}