# minuta.io

Aplicação desktop (Windows) para preencher minutas jurídicas em Word a partir de documentos
digitalizados ou PDFs, com processamento local, OCR e revisão humana obrigatória.

- Stack prevista: Tauri 2 + React/TypeScript/Vite, motor em Python (docxtpl, Tesseract, SQLite).
- Estado: Fase 1 — biblioteca de minutas, conversão de espaços `???` em campos, preenchimento
  manual e geração de Word + PDF. Ver [docs/plano-tecnico.md](docs/plano-tecnico.md).
- Como preparar uma minuta: [docs/minutas.md](docs/minutas.md).
- Como correr: [docs/desenvolvimento.md](docs/desenvolvimento.md).

> Os dados preenchidos e o documento final devem ser sempre validados pelo utilizador.
> Não colocar minutas reais nem documentos de clientes neste repositório.
