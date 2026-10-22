-- Registro auxiliar de n8n; nunca es la base de datos de la tienda.
CREATE TABLE IF NOT EXISTS pf_config (
  clave text PRIMARY KEY,
  valor text NOT NULL
);
CREATE TABLE IF NOT EXISTS pf_registro (
  clave text PRIMARY KEY,
  tipo text NOT NULL,
  estado text NOT NULL CHECK (estado IN ('reservado', 'confirmado', 'revision')),
  ejecucion text NOT NULL,
  documento jsonb NOT NULL DEFAULT '{}',
  creado timestamptz NOT NULL DEFAULT now(),
  actualizado timestamptz NOT NULL DEFAULT now()
);
-- Valores no secretos, exclusivamente para el correo local de pruebas.
INSERT INTO pf_config(clave, valor) VALUES
  ('API_BASE_URL', 'http://tienda:8000'),
  ('CORREO_MARISA', 'marisa@example.test'),
  ('CORREO_REMITENTE', 'pasofirme@example.test'),
  ('MODELO_EXTRACCION', 'openrouter/free'),
  ('CUENTA_BUZON', 'pruebas-locales')
ON CONFLICT DO NOTHING;
-- UMBRAL_VENTA_GRANDE se acuerda y se añade antes de utilizar PF-04.
