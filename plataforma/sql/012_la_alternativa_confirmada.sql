-- La alternativa confirmada: no basta con un si, hay que saber **que** se dijo que si.
--
-- Que fallaba, y con las palabras del dueno: «Guarda un si/no por linea, pero no que producto alternativo
-- aceptaste. El motor puede elegir otro manana y mantenerlo autorizado.»
--
-- Tenia razon, y el fallo era peor por como estaba argumentado: cuando escribi la 011 dije, con estas palabras,
-- que **no** se guardaba que alternativa se autorizo, y lo justifique diciendo que la elige el motor cada vez
-- con los precios de hoy. Ese argumento cubre que cambie **el precio**; no cubre que cambie **el producto**.
-- Son dos cosas distintas y las trate como una.
--
-- Por que producto **y** cadena. El producto es lo que se compra -- el identificador de la ficha -- y la cadena
-- es donde. La misma ficha en dos cadenas es la misma cosa a distinto precio, pero confirmar una sustitucion es
-- aceptar **ese** producto; saber en que cadena se confirmo permite decir *«esto lo aceptaste en DIA»* en vez
-- de dar por bueno un cambio de tienda. Se guardan las dos, y la comparacion se hace con las dos.
--
-- Por que las autorizaciones viejas se **retiran**, y esto es lo importante. Una linea marcada con `true` por la
-- 011 no dice que se autorizo: el dato de que producto se aceptaba **no existe**. Dejar ese `true` seria
-- honrar una decision que no consta, que es justo lo que el dueno senala. Asi que se apaga, y la persona vuelve
-- a confirmar **una vez**, ahora si con el producto guardado. Es preferible pedir una confirmacion de mas que
-- dar por buena una sustitucion que nadie acepto.
--
-- `IF NOT EXISTS` para que sea repetible: la aplican los contenedores al arrancar.

ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS autorizado_producto text;
ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS autorizado_cadena text;

-- Las que se autorizaron **sin constar que**: no se pueden honrar. Se apagan y se deja dicho por que.
UPDATE lista_linea
   SET autorizado = false,
       autorizado_en = NULL
 WHERE autorizado IS TRUE
   AND autorizado_producto IS NULL;

-- Y la regla, escrita en la base para que no dependa de que alguien la recuerde:
-- una linea autorizada **siempre** tiene producto.
ALTER TABLE lista_linea
  DROP CONSTRAINT IF EXISTS lista_linea_autorizado_con_producto;
ALTER TABLE lista_linea
  ADD CONSTRAINT lista_linea_autorizado_con_producto
  CHECK (autorizado IS NOT TRUE OR autorizado_producto IS NOT NULL);

COMMENT ON COLUMN lista_linea.autorizado_producto IS
    'El producto concreto que la persona acepto como sustitucion. NULL en las historicas: no consta.';
COMMENT ON COLUMN lista_linea.autorizado_cadena IS
    'La cadena en la que se acepto esa sustitucion, para poder decir donde y detectar un cambio de tienda.';
