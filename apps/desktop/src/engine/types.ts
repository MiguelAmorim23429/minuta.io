/**
 * Tipos das respostas do motor. Espelham os modelos Pydantic em
 * `engine/src/minuta_engine/models/`. Numa fase posterior passam a ser gerados a partir do
 * JSON Schema desses modelos.
 */

// Sistema -----------------------------------------------------------------------------------

export interface PingResult {
  pong: boolean;
  version: string;
}

export type CheckStatus = "ok" | "warning" | "error";

export interface Check {
  id: string;
  label: string;
  status: CheckStatus;
  detail: string;
}

export interface Diagnostics {
  engine_version: string;
  python_version: string;
  checks: Check[];
}

// Minutas -----------------------------------------------------------------------------------

export type FieldType = "text" | "multiline" | "nif" | "money" | "date";

export interface FieldSpec {
  key: string;
  label: string;
  type: FieldType;
  group_id: string;
  group_label: string;
  /** False quando o campo não consta do catálogo. */
  known: boolean;
  order: number;
}

export interface FieldGroup {
  id: string;
  label: string;
  fields: FieldSpec[];
}

export type TemplateStatus = "ready" | "needs_attention" | "missing";

export interface TemplateInfo {
  id: string;
  name: string;
  imported_at: string;
  updated_at: string;
  status: TemplateStatus;
  placeholder_count: number;
  marker_count: number;
  error_count: number;
}

export interface Location {
  part: string;
  paragraph: number;
}

export interface Issue {
  severity: "error" | "warning";
  message: string;
  location: Location | null;
  context: string;
}

export interface PlaceholderInfo {
  field: FieldSpec;
  occurrences: number;
  parts: string[];
}

export interface Marker {
  id: string;
  location: Location;
  length: number;
  before: string;
  after: string;
  convertible: boolean;
}

export interface TemplateScan {
  template: TemplateInfo;
  placeholders: PlaceholderInfo[];
  markers: Marker[];
  issues: Issue[];
}

export interface MarkerAssignment {
  marker_id: string;
  field: string;
}

// Documentos --------------------------------------------------------------------------------

export interface GenerateRequest {
  template_id: string;
  values: Record<string, string>;
  output_dir: string;
  file_name: string;
  pdf: boolean;
}

export interface GenerateResult {
  docx_path: string;
  pdf_path: string | null;
  pdf_error: string | null;
}
