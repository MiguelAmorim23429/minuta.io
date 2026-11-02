import { open } from "@tauri-apps/plugin-dialog";
import { useCallback, useEffect, useState } from "react";

import { engine, errorMessage } from "../engine/client";
import type { TemplateInfo, TemplateStatus } from "../engine/types";
import type { Navigate } from "../navigation";

const STATUS: Record<TemplateStatus, { label: string; tone: string }> = {
  ready: { label: "Pronta", tone: "ok" },
  needs_attention: { label: "Precisa de revisão", tone: "warning" },
  missing: { label: "Ficheiro em falta", tone: "error" },
};

/** Biblioteca de minutas: importar, rever, preencher, mudar o nome e remover. */
export function TemplatesPage({ navigate }: { navigate: Navigate }) {
  const [templates, setTemplates] = useState<TemplateInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null);

  const load = useCallback(async () => {
    try {
      setTemplates(await engine.templates.list());
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function importTemplate() {
    const path = await open({
      multiple: false,
      directory: false,
      title: "Escolher minuta",
      filters: [{ name: "Documento Word", extensions: ["docx"] }],
    });
    if (typeof path !== "string") {
      return;
    }
    setBusy(true);
    try {
      const info = await engine.templates.import(path);
      if (info.status === "ready") {
        await load();
      } else {
        navigate({ page: "review", templateId: info.id });
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveName() {
    if (!renaming) {
      return;
    }
    try {
      await engine.templates.rename(renaming.id, renaming.name);
      setRenaming(null);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function remove(template: TemplateInfo) {
    const confirmed = window.confirm(
      `Remover a minuta “${template.name}” da biblioteca?\n\n` +
        "O ficheiro original que importou não é apagado.",
    );
    if (!confirmed) {
      return;
    }
    try {
      await engine.templates.remove(template.id);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Minutas</h1>
          <p className="muted">As minutas guardadas na aplicação, prontas a preencher.</p>
        </div>
        <button type="button" onClick={() => void importTemplate()} disabled={busy}>
          {busy ? "A importar…" : "Importar minuta"}
        </button>
      </header>

      {error && (
        <div className="callout callout-error" role="alert">
          {error}
        </div>
      )}

      {templates === null && !error && <p className="muted">A carregar…</p>}

      {templates?.length === 0 && (
        <div className="empty">
          <strong>Ainda não há minutas.</strong>
          <p className="muted">
            Importe uma minuta Word (.docx). O ficheiro original não é alterado: a aplicação guarda
            uma cópia.
          </p>
        </div>
      )}

      {templates && templates.length > 0 && (
        <ul className="list">
          {templates.map((template) => {
            const status = STATUS[template.status];
            const isRenaming = renaming?.id === template.id;
            return (
              <li key={template.id} className="list-item">
                <div className="list-main">
                  {isRenaming ? (
                    <form
                      className="inline-form"
                      onSubmit={(event) => {
                        event.preventDefault();
                        void saveName();
                      }}
                    >
                      <input
                        autoFocus
                        value={renaming.name}
                        onChange={(event) =>
                          setRenaming({ id: template.id, name: event.target.value })
                        }
                        aria-label="Nome da minuta"
                      />
                      <button type="submit">Guardar</button>
                      <button type="button" className="secondary" onClick={() => setRenaming(null)}>
                        Cancelar
                      </button>
                    </form>
                  ) : (
                    <strong>{template.name}</strong>
                  )}
                  <p className="muted">
                    {template.placeholder_count} campo(s)
                    {template.marker_count > 0 && ` · ${template.marker_count} espaço(s) ??? por converter`}
                    {template.error_count > 0 && ` · ${template.error_count} problema(s)`}
                  </p>
                </div>
                <span className={`badge badge-${status.tone}`}>{status.label}</span>
                <div className="actions">
                  {template.status !== "missing" && (
                    <>
                      <button
                        type="button"
                        onClick={() => navigate({ page: "fill", templateId: template.id })}
                        disabled={template.status !== "ready"}
                        title={template.status !== "ready" ? "Reveja a minuta primeiro" : undefined}
                      >
                        Preencher
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => navigate({ page: "review", templateId: template.id })}
                      >
                        Rever
                      </button>
                    </>
                  )}
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setRenaming({ id: template.id, name: template.name })}
                  >
                    Mudar nome
                  </button>
                  <button type="button" className="danger" onClick={() => void remove(template)}>
                    Remover
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
