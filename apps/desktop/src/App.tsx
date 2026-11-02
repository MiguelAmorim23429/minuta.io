import { useCallback, useRef, useState } from "react";

import type { Navigate, Route } from "./navigation";
import { DiagnosticsPage } from "./pages/DiagnosticsPage";
import { FillPage } from "./pages/FillPage";
import { TemplateReviewPage } from "./pages/TemplateReviewPage";
import { TemplatesPage } from "./pages/TemplatesPage";

/** Estrutura base da aplicação: navegação lateral e ecrã atual. */
export function App() {
  const [route, setRoute] = useState<Route>({ page: "templates" });
  const dirty = useRef(false);

  const navigate: Navigate = useCallback((next) => {
    if (
      dirty.current &&
      !window.confirm("Os dados preenchidos neste ecrã vão perder-se. Sair mesmo assim?")
    ) {
      return;
    }
    dirty.current = false;
    setRoute(next);
  }, []);

  const setDirty = useCallback((value: boolean) => {
    dirty.current = value;
  }, []);

  const inTemplates = route.page !== "diagnostics";

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">minuta.io</div>
        <nav>
          <button
            type="button"
            className={`nav-item ${inTemplates ? "active" : ""}`}
            aria-current={inTemplates ? "page" : undefined}
            onClick={() => navigate({ page: "templates" })}
          >
            Minutas
          </button>
        </nav>
        <nav className="nav-bottom">
          <button
            type="button"
            className={`nav-item ${route.page === "diagnostics" ? "active" : ""}`}
            aria-current={route.page === "diagnostics" ? "page" : undefined}
            onClick={() => navigate({ page: "diagnostics" })}
          >
            Diagnóstico
          </button>
        </nav>
      </aside>
      <main className="content">
        {route.page === "templates" && <TemplatesPage navigate={navigate} />}
        {route.page === "review" && (
          <TemplateReviewPage key={route.templateId} templateId={route.templateId} navigate={navigate} />
        )}
        {route.page === "fill" && (
          <FillPage
            key={route.templateId}
            templateId={route.templateId}
            navigate={navigate}
            onDirtyChange={setDirty}
          />
        )}
        {route.page === "diagnostics" && <DiagnosticsPage />}
        <footer className="notice">
          Processamento local. Valide sempre os dados preenchidos e o documento final.
        </footer>
      </main>
    </div>
  );
}
