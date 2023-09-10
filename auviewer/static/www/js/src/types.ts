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
  default?: string,
  required?: boolean,
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
  required: boolean,
  default: string,
  options?: Array<CategoryOption>,
  selection_type?: AnnotationSelectionType
}