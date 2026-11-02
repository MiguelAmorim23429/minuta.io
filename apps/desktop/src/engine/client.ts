import { invoke } from "@tauri-apps/api/core";

import type {
  Diagnostics,
  FieldGroup,
  FieldSpec,
  GenerateRequest,
  GenerateResult,
  MarkerAssignment,
  PingResult,
  TemplateInfo,
  TemplateScan,
} from "./types";

/** Erro devolvido pelo motor ou pela ligação ao motor. A mensagem é adequada ao utilizador. */
export class EngineError extends Error {
  override name = "EngineError";
}

/** Indica se a interface está a correr dentro da aplicação Tauri (e não num browser normal). */
export function isDesktop(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

/** Chama um método JSON-RPC do motor Python através do comando Tauri `engine_call`. */
export async function call<T>(method: string, params: object = {}): Promise<T> {
  if (!isDesktop()) {
    throw new EngineError("O motor só está disponível dentro da aplicação minuta.io.");
  }
  try {
    return await invoke<T>("engine_call", { method, params });
  } catch (error) {
    throw new EngineError(typeof error === "string" ? error : String(error));
  }
}

/** Mensagem de erro para mostrar ao utilizador. */
export function errorMessage(error: unknown): string {
  return error instanceof EngineError ? error.message : "Ocorreu um erro inesperado.";
}

export const engine = {
  ping: () => call<PingResult>("system.ping"),
  diagnostics: () => call<Diagnostics>("system.diagnostics"),

  catalog: () => call<FieldGroup[]>("fields.catalog"),

  templates: {
    list: () => call<TemplateInfo[]>("templates.list"),
    import: (path: string, name?: string) => call<TemplateInfo>("templates.import", { path, name }),
    rename: (id: string, name: string) => call<TemplateInfo>("templates.rename", { id, name }),
    remove: (id: string) => call<{ deleted: boolean }>("templates.delete", { id }),
    scan: (id: string) => call<TemplateScan>("templates.scan", { id }),
    open: (id: string) => call<{ opened: boolean }>("templates.open", { id }),
    convertMarkers: (id: string, assignments: MarkerAssignment[]) =>
      call<TemplateScan>("templates.convert_markers", { id, assignments }),
    fields: (id: string) => call<FieldSpec[]>("templates.fields", { id }),
  },

  documents: {
    generate: (request: GenerateRequest) => call<GenerateResult>("documents.generate", request),
    open: (path: string) => call<{ opened: boolean }>("documents.open", { path }),
    reveal: (path: string) => call<{ opened: boolean }>("documents.reveal", { path }),
  },
};
