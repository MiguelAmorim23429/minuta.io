/** Ecrãs da aplicação. A navegação é por estado (não há URLs numa app desktop). */
export type Route =
  | { page: "templates" }
  | { page: "review"; templateId: string }
  | { page: "fill"; templateId: string }
  | { page: "diagnostics" };

export type Navigate = (route: Route) => void;
