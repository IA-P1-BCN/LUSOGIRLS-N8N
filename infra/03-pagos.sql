-- Aplicar al registro auxiliar después del esquema de PF-08.
-- Un bloqueo permanece tras un resultado incierto, hasta conciliación humana.
CREATE TABLE IF NOT EXISTS pf_bloqueos_apartado (
  apartado_id bigint PRIMARY KEY,
  correo text UNIQUE NOT NULL REFERENCES pf_registro(clave),
  creado timestamptz NOT NULL DEFAULT now()
);
