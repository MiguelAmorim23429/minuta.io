/**
 * Tipos das respostas do motor. Espelham os modelos Pydantic em
 * `engine/src/minuta_engine/models/`. Numa fase posterior passam a ser gerados a partir do
 * JSON Schema desses modelos.
 */

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
