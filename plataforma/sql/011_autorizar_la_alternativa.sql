-- Autorizar una sustitucion: que la decision sobreviva a recargar la pantalla.
--
-- Que faltaba, y con las palabras de la revision: «`Peticion.autorizado` solo viaja en la peticion». La
-- persona confirma la alternativa en la pantalla, la API la tiene en cuenta mientras contesta, y **al
-- recargar se ha perdido**: vuelve a pedir confirmacion y el total deja de contar esa linea. Una decision
-- que hay que tomar dos veces es una decision que el sistema no se cree.
--
-- Por que una columna en `lista_linea` y no un campo mas de la peticion. Porque **la decision es sobre una
-- linea**: ese producto, en esa lista. Guardarla en la peticion la ata a la pantalla, y guardarla por lista
-- la atas al dia entero. La linea es lo unico que no cambia de significado: sigue siendo la misma casilla
-- de la lista, con la misma cantidad, aunque se recargue, se cierre el navegador o se entre desde el movil.
--
-- Por que `FALSE` por defecto y **sin tocar las lineas que ya existen**. Lo que decide el total es que una
-- linea **este** autorizada, asi que el valor seguro es «no». Y las lineas historicas **no se asignan a
-- nadie**: esa regla vale igual aqui que en el diario y en el recetario. Una linea vieja no autoriza nada
-- porque su autorizacion no consta, y eso es exactamente lo que queremos que signifique.
--
-- Por que no se guarda **que** alternativa se autorizo. Porque la alternativa la elige el motor cada vez, con
-- los precios de hoy: guardar la de ayer dejaria autorizada una sustitucion que ya no se ofrece, y el total
-- contaria un producto que nadie ha confirmado. Se guarda **la decision**, no su contenido.
--
-- `IF NOT EXISTS` para que sea repetible: la aplican los contenedores al arrancar, y arrancar dos veces no
-- puede ser un error.

ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS autorizado boolean NOT NULL DEFAULT false;

-- Quien autoriza, y cuando. Sirve para dos cosas: saber de quien es la decision -- que es lo que permite
-- exigir que sea de quien pregunta -- y poder decir cuando se tomo, que es lo primero que se pregunta
-- cuando una lista lleva semanas abierta y el total no cuadra.
ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS autorizado_en timestamptz;

-- Se busca por lista y por autorizacion: la consulta que arma el total pide, para cada linea viva, si esta
-- autorizada. Sin indice eso es un recorrido de la tabla entera en cada carga de pantalla.
CREATE INDEX IF NOT EXISTS lista_linea_autorizado_idx
    ON lista_linea (lista_id, autorizado)
    WHERE borrado_en IS NULL;

COMMENT ON COLUMN lista_linea.autorizado IS
    'La persona confirmo la sustitucion propuesta para esta linea. FALSE en las historicas: no consta.';
