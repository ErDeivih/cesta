-- **017 · La despensa: lo que hay en casa, declarado -- y por que una compra no entra aqui.**
--
-- Criterio de F11 (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:108`): *«**Existencias declaradas**, ubicacion/caducidad
-- **opcional**; **compra no acredita consumo ni stock restante**.»*
--
-- **Medido el 11 de octubre de 2026, la despensa no existia** -- y lo decian **cuatro capas**: ninguna de las 13
-- tablas era de despensa, no habia `api/despensa.py`, la pantalla solo tenia **«Stock Fuera»** (*que es una
-- mecanica de cadena, no una despensa*), y `preferencia` estaba **vacia**. *Esta tabla es la primera de las
-- cuatro.*
--
-- **Tres decisiones, y las tres estan en el DDL para que la regla y la tabla no se puedan separar:**
--
-- **1. `cantidad` puede ser NULL, y NULL quiere decir «no se sabe».** *No es un cero.* **Es el segundo caso de
-- la aceptacion del criterio -- «stock desconocido» --, y por eso no se guarda como `0`:** *`0` afirmaria que no
-- queda nada, y **«no se sabe cuanto queda» y «no queda» son dos cosas distintas*** -- *la misma distincion que
-- `sin_precio` (un cero afirmaria que salio gratis) y que `diario.fuente_dato`.* **La columna es `DOUBLE
-- PRECISION` y sin `NOT NULL`, y eso es la decision, no un descuido.**
--
-- **2. No hay ninguna clave ajena a `compra`, ni ningun disparador que escriba aqui.** *Esta tabla **no sabe** de
-- compras: se llama `despensa` y guarda **lo que hay en casa**, que **se declara** -- *no se deduce de lo que se
-- compro.* **Es la regla del criterio puesta en el esquema**: *«compra no acredita consumo ni stock restante»* --
-- ***comprar algo no quiere decir que se haya consumido, ni que quede, ni que no.*** *La misma frase que
-- `core/diario.py:140` tiene escrita desde antes: **«rechaza `compra` a proposito: comprar no es comer»**.*
--
-- **Y no es una omision que se pueda arreglar luego sin darse cuenta**: *para que una compra acreditara consumo
-- habria que **anadir** el disparador, y eso es **una decision que se toma a proposito*** -- *igual que
-- `core.despensa` no tiene ninguna funcion que sume una compra, y hay una prueba que lo fija.*
--
-- **3. `usuario_id` con clave ajena, como todo lo demas.** *Una despensa es de quien es, y **la puerta la cierra
-- el mismo `_acceso` que las listas*** -- *no se anade una segunda forma de comprobar el dueno, que es donde un
-- olvido se convierte en una fuga.*
--
-- **Y `donde` y `caduca` son `TEXT` y con defecto vacio**: *el criterio dice **«opcional»**, asi que **una
-- existencia sin ubicacion y sin fecha esta completa** -- *no le falta nada; es lo que se sabe.*

CREATE TABLE IF NOT EXISTS despensa (
    usuario_id     UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    texto          TEXT NOT NULL,
    -- NULL = no se sabe cuanto. *Ver la decision 1: no es un cero.*
    cantidad       DOUBLE PRECISION,
    unidad         TEXT NOT NULL DEFAULT '',
    -- Opcionales, como pide el criterio, y vacio es «no se ha dicho» -- no «falta».
    donde          TEXT NOT NULL DEFAULT '',
    caduca         TEXT NOT NULL DEFAULT '',
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Una linea por producto y persona: declarar es decir lo que hay AHORA, asi que se sobrescribe.
    PRIMARY KEY (usuario_id, texto)
);

-- *El indice por usuario no hace falta: la clave primaria ya empieza por `usuario_id`, y todas las consultas son
-- «lo de esta persona».* **Poner uno de mas seria ruido que hay que mantener.**
