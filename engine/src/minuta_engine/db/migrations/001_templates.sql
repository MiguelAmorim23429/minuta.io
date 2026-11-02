-- Biblioteca de minutas. O ficheiro em si fica na pasta "minutas" da aplicação.
CREATE TABLE templates (
    id          TEXT PRIMARY KEY,   -- UUID; também é o nome do ficheiro guardado (<id>.docx)
    name        TEXT NOT NULL,      -- nome dado pela utilizadora
    sha256      TEXT NOT NULL,      -- hash do ficheiro guardado (deteta alterações externas)
    imported_at TEXT NOT NULL,      -- ISO 8601, UTC
    updated_at  TEXT NOT NULL       -- ISO 8601, UTC
);
