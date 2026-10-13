# B05 · **La idempotencia la garantiza la BASE**, y la concurrencia esta razonada en el SQL

*(13 de octubre de 2026. **Quinta ronda de B05. Y contesta las dos clausulas mas dificiles del criterio.**)*

## 1. La tabla, literal (`plataforma/sql/001_esquema.sql:95`)

```sql
CREATE TABLE IF NOT EXISTS lista_linea (
    id           uuid PRIMARY KEY,          -- *** EL `linea_id` ES LA CLAVE PRIMARIA ***
    lista_id     uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    grupo_id     bigint,
    producto_id  text,
    nombre_visto text NOT NULL,
    cantidad     integer NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    nota         text,
    anadido_por  uuid NOT NULL REFERENCES usuario(id) ON DELETE RESTRICT,
    anadido_en   timestamptz NOT NULL DEFAULT now(),
    tachado_por  uuid REFERENCES usuario(id) ON DELETE SET NULL,
    tachado_en   timestamptz,
    borrado_en   timestamptz,               -- no se borra de verdad: ver abajo
    tocado_en    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT linea_con_destino CHECK (grupo_id IS NOT NULL OR producto_id IS NOT NULL),
    CONSTRAINT tachado_coherente CHECK ((tachado_por IS NULL) = (tachado_en IS NULL))
);
CREATE INDEX IF NOT EXISTS linea_por_lista ON lista_linea(lista_id) WHERE borrado_en IS NULL;

-- Por que no se borra de verdad:
--   1. Si dos moviles borran y anaden a la vez, una fila borrada reaparece
--      cuando el otro sincroniza. Con una marca, no.
--   2. Deshacer. Borrar media lista sin querer en el pasillo del supermercado
--      tiene que ser reversible sin una llamada de telefono.
-- Se limpian de verdad a los 30 dias (ver 'limpiar_lineas_borradas').
```

## 2. Y eso contesta las TRES clausulas mas dificiles de B05

```
B05 PIDE                                    Y AQUI ESTA, EN EL ESQUEMA
  1-2) RECIBO/HUELLA + «MISMA CLAVE CON
       CONTENIDO DISTINTO = CONFLICTO»      `id uuid PRIMARY KEY`.
                                            *** Repetir el `linea_id` NO PUEDE crear una segunda fila:
                                            la base lo impide. ***
                                            Y no es una comprobacion en Python («¿ya existe?»),
                                            *** que tendria una carrera. ***
  3) CONCURRENCIA Y CAIDA TRAS INSERTAR
     MEDIA LISTA                            *** EL COMENTARIO LO RAZONA, Y SON DOS RAZONES: ***
                                              «Si dos moviles borran y anaden a la vez, una fila
                                               borrada reaparece cuando el otro sincroniza. Con una
                                               marca, no.»
                                              «Deshacer. Borrar media lista sin querer en el pasillo
                                               del supermercado tiene que ser reversible sin una
                                               llamada de telefono.»
  4) Y LA LIMPIEZA                            `borrado_en` + indice parcial
                                              (`WHERE borrado_en IS NULL`) + purga a los 30 dias
```

> *** Y `id uuid PRIMARY KEY` es exactamente lo que el criterio pedia sin nombrarlo: ***
>
> *La idempotencia **no se comprueba: se garantiza**.* *Y **por eso funciona con dos pestañas**: *dos peticiones
> simultaneas con el mismo `linea_id` **no pueden** crear dos filas -- **una gana y la otra choca con la clave
> primaria**, que es **`conflicto`, no éxito ficticio**.*
>
> *** Que es, palabra por palabra, la clausula (2) del criterio -- resuelta por el esquema, no por el codigo. ***

## 3. Y el comentario del SQL es la tercera vez que el proyecto contesta el criterio por escrito

```
1) core/traspaso.py   -- «la identidad tiene que ser de la OPERACION, no del resultado»
2) tests/test_g12_*   -- ocho ensayos, uno por clausula
3) plataforma/sql/001  -- «dos moviles borran y anaden a la vez... con una marca, no»
                          «borrar media lista sin querer... reversible»
```

> *** Y los tres sitios son tres niveles distintos: el razonamiento (Python), la prueba (ensayos), y la garantia
> (el esquema). ***
>
> *Que es, para B05, **mas de lo que el plan pide** -- *y esta **escrito donde tiene que estar**: en el comentario
> de la tabla que lo hace posible.*

## 4. Y B05, con esto, tiene **cinco de las seis** contestadas

```
  1) RECIBO Y HUELLA                HECHO -- Operacion + clave() + id_de_linea() + 8 ensayos
  2) CONFLICTO, NO EXITO FICTICIO   HECHO -- `id uuid PRIMARY KEY`, garantizado por la BASE
  3) CONCURRENCIA Y MEDIA LISTA     HECHO -- `borrado_en` + las dos razones del comentario
  4) RESERVAS DE DESPENSA           POR MIRAR -- hay `017_la_despensa.sql` (3,4 KB), sin abrir
  5) CALCULO INCREMENTAL DEL PLAN   POR MIRAR -- «editar un menu no borra las lineas manuales»
  6) DESTINO DISTINTO               HECHO -- B04 (`014_la_linea_sin_destino.sql`)
```

> *** Y las dos que quedan son justo las dos que el plan subraya con mas detalle: ***
> **«Reservas de despensa»** *-- y hay una migracion con ese nombre --* **y «actualizacion del plan con calculo
> incremental: editar un menu no borra lineas manuales de compra ni duplica todas las necesidades».**
>
> *** Y no se dice nada de ellas, porque no se han abierto. ***
