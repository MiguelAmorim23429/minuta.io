import { invoke } from "@tauri-apps/api/core";

import type { Diagnostics, PingResult } from "./types";

/** Erro devolvido pelo motor ou pela ligação ao motor. A mensagem é adequada ao utilizador. */
export class EngineError extends Error {
  override name = "EngineError";
}

/** Indica se a interface está a correr dentro da aplicação Tauri (e não num browser normal). */
export function isDesktop(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

/** Chama um método JSON-RPC do motor Python através do comando Tauri `engine_call`. */
export async function call<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  if (!isDesktop()) {
    throw new EngineError("O motor só está disponível dentro da aplicação minuta.io.");
  }
  try {
    return await invoke<T>("engine_call", { method, params });
  } catch (error) {
    throw new EngineError(typeof error === "string" ? error : String(error));
  }
}

export const engine = {
  ping: () => call<PingResult>("system.ping"),
  diagnostics: () => call<Diagnostics>("system.diagnostics"),
};
