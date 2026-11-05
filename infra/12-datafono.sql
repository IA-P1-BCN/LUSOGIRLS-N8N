-- Una venta ya existente no puede confirmar dos referencias distintas del datáfono.
-- Aplicar después de registro.sql en el registro auxiliar, nunca en SQLite.
CREATE UNIQUE INDEX IF NOT EXISTS pf_datafono_venta_unica
ON pf_registro (((documento->>'venta_id')::bigint))
WHERE tipo='datafono' AND estado='confirmado' AND documento->>'venta_id' IS NOT NULL;
