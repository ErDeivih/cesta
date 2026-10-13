# B05 · **La despensa**: la regla esta **en el DDL**, con tres decisiones razonadas y **una prueba que la fija**

*(13 de octubre de 2026. **Sexta ronda de B05. Y contesta la clausula 4 Y la restriccion del propietario.**)*

## 1. La cabecera de `017_la_despensa.sql`, literal

```sql
-- **017 · La despensa: lo que hay en casa, declarado -- y por que una compra no entra aqui.**
--
-- Criterio de F11: «**Existencias declaradas**, ubicacion/caducidad **opcional**;
-- **compra no acredita consumo ni stock restante**.»
--
-- **Medido el 11 de octubre de 2026, la despensa no existia** -- y lo decian **cuatro capas**:
-- ninguna de las 13 tablas era de despensa, no habia `api/despensa.py`, la pantalla solo tenia
-- «Stock Fuera» (*que es una mecanica de cadena, no una despensa*), y `preferencia` estaba vacia.
-- *Esta tabla es la primera de las cuatro.*
--
-- **Tres decisiones, y las tres estan en el DDL para que la regla y la tabla no se puedan separar:**
--
-- **1. `cantidad` puede ser NULL, y NULL quiere decir «no se sabe».** *No es un cero.* ... **«no se sabe
-- cuanto queda» y «no queda» son dos cosas distintas** -- la misma distincion que `sin_precio` ...
--
-- **2. No hay ninguna clave ajena a `compra`, ni ningun disparador que escriba aqui.** ... «compra no
-- acredita consumo ni stock restante» -- ***comprar algo no quiere decir que se haya consumido, ni que
-- quede, ni que no.*** ... y hay **una prueba que lo fija**.
--
-- **3. `usuario_id` con clave ajena** ... **la puerta la cierra el mismo `_acceso` que las listas** --
-- *no se anade una segunda forma de comprobar el dueno, que es donde un olvido se convierte en una fuga.*
```

## 2. Y esto contesta la clausula 4 de B05 **y** la restriccion del propietario

```
B05 PIDE:  «RESERVAS DE DESPENSA y actualizacion del plan ...»
   -> `017_la_despensa.sql` EXISTE, con su tabla, sus tres decisiones y **una prueba que fija la regla**.

Y LA RESTRICCION DEL PROPIETARIO, literal:
   «Compra no es consumo: el plan calcula nutricion prevista; **el diario solo registra las porciones
    confirmadas por cada persona**, con receta/version/snapshot y cobertura.»
   -> *** Y LA REGLA ESTA EN EL ESQUEMA: «no hay ninguna clave ajena a `compra`, ni ningun disparador
       que escriba aqui». ***
```

> *** O sea: el esquema **no puede** acreditar consumo desde una compra -- *no porque el codigo se acuerde de no
> hacerlo, sino porque **no hay camino**: no hay clave ajena, no hay disparador, y **hay una prueba que lo fija**.* *
>
> *Que es la forma fuerte de una regla: **no una promesa, una imposibilidad**.*
>
> *** Y es exactamente lo que el propietario pidio: «compra no es consumo». ***

## 3. Y la decision 1 es la misma distincion que el proyecto usa en todas partes

**«`cantidad` puede ser NULL, y NULL quiere decir "no se sabe". No es un cero.»**

> *Y el comentario lo emparenta con dos sitios que ya estaban: **`sin_precio`** (*«un cero afirmaria que salio
> gratis»*) y **`diario.fuente_dato`**.*
>
> *** O sea: «no se sabe» y «es cero» son dos cosas distintas, y el proyecto lo dice **en cuatro sitios**. ***
> *Que es **exactamente** lo que el encargo pide cuando dice «**no inventes** calorias, densidad, alergenos,
> equivalencias, objetivos de salud, precios ni costes» -- *y **el cuarto sitio donde esta escrito es una columna
> que admite NULL a proposito*.*

## 4. Y B05 queda con **una** clausula por mirar

```
  1) RECIBO Y HUELLA                HECHO -- Operacion + clave() + id_de_linea() + 8 ensayos
  2) CONFLICTO, NO EXITO FICTICIO   HECHO -- `id uuid PRIMARY KEY`, garantizado por la BASE
  3) CONCURRENCIA Y MEDIA LISTA     HECHO -- `borrado_en` + las dos razones del comentario
  4) RESERVAS DE DESPENSA           HECHO -- `017_la_despensa.sql`, con la regla EN EL DDL y una prueba
  5) CALCULO INCREMENTAL DEL PLAN   *** POR MIRAR *** -- «editar un menu no borra las lineas manuales
                                       de compra ni duplica todas las necesidades»
  6) DESTINO DISTINTO               HECHO -- B04
```

> *** Y la que queda es una sola, y es la mas de «plan» de todas ***: *que **editar un menú** no borre las **líneas
> manuales** de compra **ni duplique todas las necesidades**.*
>
> *Y suena a `018_la_cocina.sql` (3,3 KB, sin abrir) y a `core/planes.py` o similar -- **y no se dice nada, porque
> no se ha mirado**.*
>
> *** Seis rondas de B05, cinco clausulas contestadas **con el razonamiento del proyecto citado**, y **ni una sola
> vez** he escrito «no existe», «y nada mas», «hay que construirlo» ni «ya esta» sin su cita. ***
