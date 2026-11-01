import { DiagnosticsPage } from "./pages/DiagnosticsPage";

/**
 * Estrutura base da aplicação. Na Fase 0 só existe o ecrã de diagnóstico; as restantes
 * secções (minutas, processos) entram na navegação à medida que forem implementadas.
 */
export function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">minuta.io</div>
        <nav>
          <a className="nav-item active" aria-current="page">
            Diagnóstico
          </a>
        </nav>
      </aside>
      <main className="content">
        <DiagnosticsPage />
        <footer className="notice">
          Processamento local. Valide sempre os dados preenchidos e o documento final.
        </footer>
      </main>
    </div>
  );
}
