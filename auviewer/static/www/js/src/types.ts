// Serialized business logic

export interface Annotation {
  project_id: number,
  file_id: number,
  left: number,
  right: number, 
  series_id: string,
  label: string,
  pattern_id?: number
}

export interface LabelerEvaluativeStats {
  labeler: string,
  coverage: number,
  conflicts: number,
  polarity: Array<number>,
  experimental_accuracy?: number,
  empirical_accuracy?: number
}

export enum AnnotationFieldType {
  Categorical="categorical",
  Text="text",
  Numeric="numeric"
}

export enum AnnotationSelectionType {
  Button="button",
  Radio="radio"
}

export interface AnnotationField {
  id: string,
  label: string,
  type: AnnotationFieldType,
  classes?: Array<string>,
  class_ids?: Array<string>,
  selection_type?: AnnotationSelectionType
}


// Deserialized rendering logic
export interface CategoryOption {
  text: string,
  value: string
}

export interface AnnotationFormInput {
  id: string,
  name: string,
  type: AnnotationFieldType,
  options?: Array<CategoryOption>,
  selection_type?: AnnotationSelectionType
}