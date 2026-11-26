-- Issue #36: permitir fotografías JPEG/Base64 en denuncias.

-- Requiere que la tabla abandoned_waste_reports ya exista.
-- La operación conserva los registros existentes, ejecutar una sola vez por entorno, o repetir si es necesario.

BEGIN;

ALTER TABLE public.abandoned_waste_reports
    ALTER COLUMN photo_evidence_url TYPE TEXT;

COMMIT;