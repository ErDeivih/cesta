-- Una alerta por persona, grupo y tipo.
--
-- Sin esta restriccion, pulsar dos veces la campana deja dos avisos identicos y
-- el dia que salten llegan por duplicado. Con ella, repetir la alerta la
-- actualiza: cambiar el umbral es volver a crearla.
CREATE UNIQUE INDEX IF NOT EXISTS alerta_unica
    ON alerta(usuario_id, grupo_id, tipo);

-- Las que todavia no se han contado, que es lo unico que se consulta a diario.
CREATE INDEX IF NOT EXISTS alerta_sin_ver
    ON alerta(usuario_id) WHERE vista_en IS NULL;
