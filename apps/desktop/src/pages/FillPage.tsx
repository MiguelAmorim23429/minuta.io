import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useMemo, useState } from "react";

import { engine, errorMessage } from "../engine/client";
import type { FieldSpec, GenerateResult, TemplateInfo } from "../engine/types";
import { loadPreference, savePreference } from "../lib/storage";
import { isValidNif } from "../lib/validation";
import type { Navigate } from "../navigation";

const OUTPUT_DIR_KEY = "outputDir";

const HINTS: Partial<Record<FieldSpec["type"], string>> = {
  nif: "9 algarismos",
  money: "ex.: € 150.000,00",
  date: "ex.: 12/10/2026",
};

interface Group {
  id: string;
  label: string;
  fields: FieldSpec[];
}

/**
 * Preenchimento manual de uma minuta e geração do documento (Word e, opcionalmente, PDF).
 * Os valores ficam apenas em memória enquanto o ecrã está aberto.
 */
export function FillPage({
  templateId,
  navigate,
  onDirtyChange,
}: {
  templateId: string;
  navigate: Navigate;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const [template, setTemplate] = useState<TemplateInfo | null>(null);
  const [fields, setFields] = useState<FieldSpec[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [blank, setBlank] = useState<Record<string, boolean>>({});
  const [outputDir, setOutputDir] = useState<string>(() => loadPreference(OUTPUT_DIR_KEY) ?? "");
  const [fileName, setFileName] = useState("");
  const [pdf, setPdf] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResult | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [scan, specs] = await Promise.all([
          engine.templates.scan(templateId),
          engine.templates.fields(templateId),
        ]);
        if (cancelled) {
          return;
        }
        setTemplate(scan.template);
        setFields(specs);
        setFileName(`${scan.template.name} - ${new Date().toLocaleDateString("pt-PT").replaceAll("/", "-")}`);
      } catch (e) {
        if (!cancelled) {
          setError(errorMessage(e));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [templateId]);

  const dirty = Object.values(values).some((value) => value.trim() !== "");
  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);
  useEffect(() => () => onDirtyChange(false), [onDirtyChange]);

  const groups = useMemo(() => {
    const byId = new Map<string, Group>();
    for (const field of fields) {
      const group = byId.get(field.group_id) ?? { id: field.group_id, label: field.group_label, fields: [] };
      group.fields.push(field);
      byId.set(field.group_id, group);
    }
    return [...byId.values()];
  }, [fields]);

  const pending = fields.filter((field) => !blank[field.key] && !(values[field.key] ?? "").trim());
  const canGenerate = pending.length === 0 && outputDir !== "" && fileName.trim() !== "" && !busy;

  function setValue(key: string, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
    setResult(null);
  }

  function toggleBlank(key: string, checked: boolean) {
    setBlank((current) => ({ ...current, [key]: checked }));
    setResult(null);
  }

  async function chooseFolder() {
    const folder = await open({ directory: true, multiple: false, title: "Pasta de destino" });
    if (typeof folder === "string") {
      setOutputDir(folder);
      savePreference(OUTPUT_DIR_KEY, folder);
    }
  }

  async function generate() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const filled: Record<string, string> = {};
      for (const field of fields) {
        filled[field.key] = blank[field.key] ? "" : (values[field.key] ?? "").trim();
      }
      setResult(
        await engine.documents.generate({
          template_id: templateId,
          values: filled,
          output_dir: outputDir,
          file_name: fileName,
          pdf,
        }),
      );
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function openPath(action: "open" | "reveal", path: string) {
    try {
      await engine.documents[action](path);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (!template) {
    return (
      <section className="page">
        {error ? (
          <div className="callout callout-error" role="alert">
            {error}
          </div>
        ) : (
          <p className="muted">A carregar a minuta…</p>
        )}
      </section>
    );
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <button type="button" className="link" onClick={() => navigate({ page: "templates" })}>
            ← Minutas
          </button>
          <h1>{template.name}</h1>
          <p className="muted">Preenchimento</p>
        </div>
      </header>

      {template.status !== "ready" && (
        <div className="callout callout-warning">
          Esta minuta precisa de revisão antes de ser preenchida.{" "}
          <button type="button" className="link" onClick={() => navigate({ page: "review", templateId })}>
            Rever minuta
          </button>
        </div>
      )}

      <div className="callout callout-info">
        Os dados escritos aqui não são guardados: ficam apenas neste ecrã até gerar o documento.
      </div>

      {groups.map((group) => (
        <fieldset key={group.id} className="card group">
          <legend>{group.label}</legend>
          {group.fields.map((field) => (
            <FieldInput
              key={field.key}
              field={field}
              value={values[field.key] ?? ""}
              blank={blank[field.key] ?? false}
              onChange={(value) => setValue(field.key, value)}
              onBlankChange={(checked) => toggleBlank(field.key, checked)}
            />
          ))}
        </fieldset>
      ))}

      <div className="card">
        <h2>Gerar documento</h2>
        <div className="field">
          <label>Pasta de destino</label>
          <div className="inline-form">
            <input value={outputDir} readOnly placeholder="Escolha uma pasta" aria-label="Pasta de destino" />
            <button type="button" className="secondary" onClick={() => void chooseFolder()}>
              Escolher…
            </button>
          </div>
        </div>
        <div className="field">
          <label htmlFor="file-name">Nome do ficheiro</label>
          <input id="file-name" value={fileName} onChange={(event) => setFileName(event.target.value)} />
        </div>
        <label className="checkbox">
          <input type="checkbox" checked={pdf} onChange={(event) => setPdf(event.target.checked)} />
          Criar também PDF (usa o Microsoft Word)
        </label>

        {pending.length > 0 && (
          <p className="field-warning">
            Faltam {pending.length} campo(s). Preencha-os ou marque “Deixar em branco”.
          </p>
        )}

        {error && (
          <div className="callout callout-error" role="alert">
            {error}
          </div>
        )}

        <div className="actions end">
          <button type="button" disabled={!canGenerate} onClick={() => void generate()}>
            {busy ? "A gerar…" : "Gerar documento"}
          </button>
        </div>

        {result && (
          <div className="callout callout-ok result">
            <strong>Documento gerado.</strong>
            <p>Reveja sempre o documento final antes de o utilizar.</p>
            <div className="actions">
              <button type="button" onClick={() => void openPath("open", result.docx_path)}>
                Abrir Word
              </button>
              {result.pdf_path && (
                <button type="button" onClick={() => void openPath("open", result.pdf_path!)}>
                  Abrir PDF (imprimir)
                </button>
              )}
              <button type="button" className="secondary" onClick={() => void openPath("reveal", result.docx_path)}>
                Mostrar na pasta
              </button>
            </div>
            {result.pdf_error && <p className="field-warning">{result.pdf_error}</p>}
          </div>
        )}
      </div>
    </section>
  );
}

function FieldInput({
  field,
  value,
  blank,
  onChange,
  onBlankChange,
}: {
  field: FieldSpec;
  value: string;
  blank: boolean;
  onChange: (value: string) => void;
  onBlankChange: (checked: boolean) => void;
}) {
  const id = `field-${field.key}`;
  const nifWarning = field.type === "nif" && value.trim() !== "" && !isValidNif(value);
  const common = {
    id,
    value: blank ? "" : value,
    disabled: blank,
    placeholder: HINTS[field.type],
    onChange: (event: { target: { value: string } }) => onChange(event.target.value),
  };

  return (
    <div className="field">
      <div className="field-header">
        <label htmlFor={id}>{field.label}</label>
        <label className="checkbox small">
          <input type="checkbox" checked={blank} onChange={(event) => onBlankChange(event.target.checked)} />
          Deixar em branco
        </label>
      </div>
      {field.type === "multiline" ? <textarea rows={2} {...common} /> : <input {...common} />}
      {nifWarning && (
        <p className="field-warning">O número não passa na validação do dígito de controlo. Confirme.</p>
      )}
    </div>
  );
}
