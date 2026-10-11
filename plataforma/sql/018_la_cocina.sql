-- **018 · La cocina: por donde ibas, y los temporizadores como HORAS DE FIN.**
--
-- Criterio de F10 (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:105`): *«**Paso actual, ingredientes usados,
-- temporizadores** y **reanudacion sin conexion cuando sea viable**.»*
--
-- **Medido el 11 de octubre de 2026, el modo cocina no existia** -- y lo mejor del hallazgo fue que **el propio
-- proyecto lo dijo sin querer**: `plataforma/prueba_navegador.py:603`, *«y no es una visita guiada: **no hay pasos
-- que pasar**»*. *La logica esta en `core/cocina.py`, con 10 pruebas; esta tabla es donde vive.*
--
-- **Tres decisiones, y la primera es la que da sentido a la tabla:**
--
-- **1. Los temporizadores guardan CUANDO EMPEZARON, no cuanto queda.** *Es la decision central de
-- `core/cocina.py`, y esta aqui para que no se pueda perder por el camino:*
--
--     **Un temporizador NO es una cuenta atras.** *Una cuenta atras vive en la pantalla y **muere con ella**: si
--     se apaga el movil, o se recarga, o se va la conexion, **el tiempo transcurrido se pierde** -- y quien esta
--     cocinando **no se entera** hasta que algo se quema.*
--
--     **Un temporizador es una hora de fin.** *Se guarda `empezo_en` y `minutos`, y **lo que queda se calcula**.
--     Asi **reanudar es volver a leer**, y **funciona sin conexion** porque **no hay nada que consultar**: el
--     reloj lo lleva el aparato.*
--
-- **Asi que la columna se llama `temporizadores` y lleva instantes, no segundos restantes.** *Si llevara
-- «cuanto queda», **habria que ir restando** -- y eso exige que alguien este mirando, que es exactamente lo que
-- no se puede garantizar.* **La forma de la columna es la decision.**
--
-- **2. `paso` puede ser NULL, y NULL quiere decir «sin empezar».** *No es el paso 0.* **«No he empezado» y «voy
-- por el primero» se dicen distinto**, y por eso el paso empieza en `NULL` -- *la misma forma que
-- `despensa.cantidad` (que es NULL cuando no se sabe), y por la misma razon: **un cero es una afirmacion**.*
--
-- **3. La clave es `(usuario_id, receta_id)` con la VERSION dentro.** *`receta_id` dice **que** se esta
-- cocinando y `version` **cual de sus versiones** -- *que es lo que hace que una receta reescrita **no cambie lo
-- que estabas cocinando**.* **Es la misma decision que `diario.entrada.version`** (*una receta se anota con su
-- version: sin ella no se puede releer*), y por eso **la version es `NOT NULL`**.
--
-- *Una sesion de cocina por receta y persona: **volver a la misma receta es seguir donde ibas**, no empezar
-- otra. Si algun dia hacen falta varias a la vez, eso es una decision y se vera aqui.*

CREATE TABLE IF NOT EXISTS cocina (
    usuario_id     UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    receta_id      INTEGER NOT NULL,
    -- *Cual de las versiones: una receta reescrita no cambia lo que estabas cocinando.*
    version        INTEGER NOT NULL,
    -- NULL = sin empezar. *No es el paso 0.*
    paso           INTEGER,
    -- Los ingredientes ya echados, por lo que dice la receta. *No dos veces: echar la sal en dos pasos no es
    -- echar el doble.*
    usados         TEXT[] NOT NULL DEFAULT '{}',
    -- **Instantes, no cuentas atras.** *Ver la decision 1: [{paso, minutos, empezo_en}].*
    temporizadores JSONB NOT NULL DEFAULT '[]'::jsonb,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (usuario_id, receta_id)
);
