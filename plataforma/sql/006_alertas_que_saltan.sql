-- Cuando una alerta salta de verdad, sin que nadie haya abierto la pantalla.
--
-- `vista_en` es "esta persona lo ha visto", y hasta hoy era el unico reloj de la
-- tabla: la condicion de una alerta se comprobaba al abrir `GET /api/alertas`, asi
-- que el aviso saltaba si entrabas a mirar. Con `salto_en` se apunta **cuando se
-- cumplio la condicion**, lo mire quien lo mire, y lo hace el vigilante
-- (`api/vigilante.py`) en cuanto gold cambia.
--
-- Son dos cosas distintas y por eso son dos columnas: una no puede hacer el trabajo
-- de la otra sin mentir.
ALTER TABLE alerta ADD COLUMN IF NOT EXISTS salto_en timestamptz;

-- Y **la frase que la explica, guardada en el momento en que salto**. No es un adorno:
-- la frase se calcula contra el gold de ese dia, y gold se reescribe cada manana. Si no
-- se guarda, manana la misma alerta contaria otra cosa -- o ninguna --, y el aviso que
-- alguien vio ayer cambiaria de texto solo. Es ademas lo que pide el encargo: *"dejar el
-- resultado guardado, para que abrir la aplicacion sea instantaneo"*.
ALTER TABLE alerta ADD COLUMN IF NOT EXISTS salto_texto text;

-- Lo que mira el vigilante en cada pasada: las que no han saltado y nadie ha visto.
-- Es un indice parcial porque el caso normal es que esta lista este vacia.
CREATE INDEX IF NOT EXISTS alerta_por_saltar
    ON alerta(salto_en) WHERE salto_en IS NULL AND vista_en IS NULL;
