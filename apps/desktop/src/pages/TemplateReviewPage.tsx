import { useCallback, useEffect, useMemo, useState } from "react";

import { engine, errorMessage } from "../engine/client";
import type { FieldGroup, Marker, TemplateScan } from "../engine/types";
import type { Navigate } from "../navigation";

const CUSTOM = "__custom__";
const FIELD_NAME = /^[a-z][a-z0-9_]*$/;

interface Choice {
  field: string; // chave do catálogo, CUSTOM ou "" (não converter)
  custom: string;
}

/**
 * Revisão de uma minuta: problemas encontrados, conversão dos espaços `???` em campos e
 * lista dos campos que serão pedidos no preenchimento.
 */
export function TemplateReviewPage({
  templateId,
  navigate,
}: {
  templateId: string;
  navigate: Navigate;
}) {
  const [scan, setScan] = useState<TemplateScan | null>(null);
  const [catalog, setCatalog] = useState<FieldGroup[]>([]);
  const [choices, setChoices] = useState<Record<string, Choice>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [result, groups] = await Promise.all([
        engine.templates.scan(templateId),
        engine.catalog(),
      ]);
      setScan(result);
      setCatalog(groups);
      setChoices({});
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [templateId]);

  useEffect(() => {
    void load();
  }, [load]);

  const assignments = useMemo(() => {
    return Object.entries(choices)
      .map(([markerId, choice]) => ({
        marker_id: markerId,
        field: choice.field === CUSTOM ? choice.custom.trim() : choice.field,
      }))
      .filter((assignment) => assignment.field !== "");
  }, [choices]);

  const invalidNames = assignments.filter((a) => !FIELD_NAME.test(a.field));
  const usedFields = new Set([
    ...(scan?.placeholders.map((p) => p.field.key) ?? []),
    ...assignments.map((a) => a.field),
  ]);

  function setChoice(markerId: string, update: Partial<Choice>) {
    setChoices((current) => ({
      ...current,
      [markerId]: { field: "", custom: "", ...current[markerId], ...update },
    }));
  }

  async function convert() {
    setBusy(true);
    try {
      setScan(await engine.templates.convertMarkers(templateId, assignments));
      setChoices({});
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function openInWord() {
    try {
      await engine.templates.open(templateId);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (!scan) {
    return (
      <section className="page">
        {error ? (
          <div className="callout callout-error" role="alert">
            {error}
          </div>
        ) : (
          <p className="muted">A analisar a minuta…</p>
        )}
      </section>
    );
  }

  const errors = scan.issues.filter((issue) => issue.severity === "error");
  const ready = scan.template.status === "ready";

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <button type="button" className="link" onClick={() => navigate({ page: "templates" })}>
            ← Minutas
          </button>
          <h1>{scan.template.name}</h1>
          <p className="muted">Revisão da minuta</p>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={() => void openInWord()}>
            Editar no Word
          </button>
          <button type="button" className="secondary" onClick={() => void load()}>
            Analisar novamente
          </button>
          <button
            type="button"
            disabled={!ready}
            onClick={() => navigate({ page: "fill", templateId })}
          >
            Preencher
          </button>
        </div>
      </header>

      {error && (
        <div className="callout callout-error" role="alert">
          {error}
        </div>
      )}

      {ready && (
        <div className="callout callout-ok">
          A minuta está pronta a preencher ({scan.placeholders.length} campos).
        </div>
      )}

      {errors.length > 0 && (
        <div className="card">
          <h2>Problemas a corrigir no Word</h2>
          <p className="muted">
            Use “Editar no Word”, corrija e grave o documento, depois “Analisar novamente”.
          </p>
          <ul className="issues">
            {errors.map((issue, index) => (
              <li key={index}>
                <strong>{issue.message}</strong>
                {issue.location && (
                  <span className="muted">
                    {" "}
                    — {issue.location.part}, parágrafo {issue.location.paragraph}
                  </span>
                )}
                {issue.context && <p className="context">{issue.context}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {scan.markers.length > 0 && (
        <div className="card">
          <h2>Espaços por preencher ({scan.markers.length})</h2>
          <p className="muted">
            Escolha o campo que corresponde a cada espaço marcado com ???. Só o marcador é
            substituído; o texto da minuta fica igual.
          </p>
          <ul className="markers">
            {scan.markers.map((marker) => (
              <MarkerRow
                key={marker.id}
                marker={marker}
                catalog={catalog}
                choice={choices[marker.id]}
                usedFields={usedFields}
                onChange={(update) => setChoice(marker.id, update)}
              />
            ))}
          </ul>
          {invalidNames.length > 0 && (
            <p className="field-warning">
              Nomes de campo novos: só letras minúsculas sem acentos, algarismos e _ (ex.:
              nome_banco).
            </p>
          )}
          <div className="actions end">
            <button
              type="button"
              disabled={busy || assignments.length === 0 || invalidNames.length > 0}
              onClick={() => void convert()}
            >
              {busy ? "A converter…" : `Converter ${assignments.length} espaço(s)`}
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Campos da minuta ({scan.placeholders.length})</h2>
        {scan.placeholders.length === 0 ? (
          <p className="muted">Ainda não há campos {"{{ … }}"} nesta minuta.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Campo</th>
                <th>Nome técnico</th>
                <th>Ocorrências</th>
              </tr>
            </thead>
            <tbody>
              {scan.placeholders.map((placeholder) => (
                <tr key={placeholder.field.key}>
                  <td>
                    {placeholder.field.label}{" "}
                    {!placeholder.field.known && <span className="tag">fora do catálogo</span>}
                  </td>
                  <td>
                    <code>{placeholder.field.key}</code>
                  </td>
                  <td>{placeholder.occurrences}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted small">
          Se a minuta ainda tiver dados de um caso concreto escritos (nomes, datas, números),
          substitua-os no Word por {"{{ nome_do_campo }}"}, escrito de seguida.
        </p>
      </div>
    </section>
  );
}

function MarkerRow({
  marker,
  catalog,
  choice,
  usedFields,
  onChange,
}: {
  marker: Marker;
  catalog: FieldGroup[];
  choice: Choice | undefined;
  usedFields: Set<string>;
  onChange: (update: Partial<Choice>) => void;
}) {
  return (
    <li className="marker">
      <p className="context">
        {marker.before.length >= 70 && "…"}
        {marker.before}
        <mark>{"?".repeat(Math.min(marker.length, 12))}</mark>
        {marker.after}
        {marker.after.length >= 70 && "…"}
      </p>
      <div className="marker-controls">
        <span className="muted small">
          {marker.location.part}, parágrafo {marker.location.paragraph}
        </span>
        {marker.convertible ? (
          <>
            <select
              value={choice?.field ?? ""}
              onChange={(event) => onChange({ field: event.target.value })}
              aria-label="Campo para este espaço"
            >
              <option value="">— não converter —</option>
              {catalog.map((group) => (
                <optgroup key={group.id} label={group.label}>
                  {group.fields.map((field) => (
                    <option key={field.key} value={field.key}>
                      {field.label}
                      {usedFields.has(field.key) && field.key !== choice?.field ? " (já usado)" : ""}
                    </option>
                  ))}
                </optgroup>
              ))}
              <option value={CUSTOM}>Outro campo (escrever nome)…</option>
            </select>
            {choice?.field === CUSTOM && (
              <input
                placeholder="nome_do_campo"
                value={choice.custom}
                onChange={(event) => onChange({ custom: event.target.value })}
                aria-label="Nome do novo campo"
              />
            )}
          </>
        ) : (
          <span className="muted small">Não é possível converter nesta parte do documento.</span>
        )}
      </div>
    </li>
  );
}
