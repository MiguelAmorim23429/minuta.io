import { useCallback, useEffect, useState } from "react";

import { engine, EngineError } from "../engine/client";
import type { CheckStatus, Diagnostics } from "../engine/types";

type State =
  | { kind: "loading" }
  | { kind: "ready"; data: Diagnostics }
  | { kind: "failed"; message: string };

const STATUS_LABEL: Record<CheckStatus, string> = {
  ok: "OK",
  warning: "Atenção",
  error: "Erro",
};

/** Mostra se o motor responde e se as ferramentas externas (OCR, Word) estão disponíveis. */
export function DiagnosticsPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "ready", data: await engine.diagnostics() });
    } catch (error) {
      const message = error instanceof EngineError ? error.message : "Erro inesperado.";
      setState({ kind: "failed", message });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Diagnóstico</h1>
          <p className="muted">Verifica se o computador tem tudo o que a aplicação precisa.</p>
        </div>
        <button type="button" onClick={() => void load()} disabled={state.kind === "loading"}>
          Verificar novamente
        </button>
      </header>

      {state.kind === "loading" && <p className="muted">A verificar…</p>}

      {state.kind === "failed" && (
        <div className="callout callout-error" role="alert">
          <strong>Não foi possível contactar o motor.</strong>
          <p>{state.message}</p>
        </div>
      )}

      {state.kind === "ready" && (
        <>
          <ul className="checks">
            <li className="check">
              <span className="badge badge-ok">{STATUS_LABEL.ok}</span>
              <div>
                <strong>Motor de processamento</strong>
                <p className="muted">
                  Versão {state.data.engine_version} · Python {state.data.python_version}
                </p>
              </div>
            </li>
            {state.data.checks.map((check) => (
              <li key={check.id} className="check">
                <span className={`badge badge-${check.status}`}>{STATUS_LABEL[check.status]}</span>
                <div>
                  <strong>{check.label}</strong>
                  <p className="muted">{check.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
