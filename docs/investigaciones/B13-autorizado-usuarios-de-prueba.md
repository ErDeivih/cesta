# B13 · **Autorizado por el dueño**: usuarios de prueba en `cesta-db-1` -- y el procedimiento exacto

*(13 de octubre de 2026. **Tercera ronda de B13. Y la primera decision del encargo que no se resuelve leyendo.**)*

## 1. La pregunta, y la respuesta

```
PREGUNTA:  B13 necesita «cinco recorridos con usuarios de prueba, NO cuentas reales».
           ¿Como procedo, sin tocar nada tuyo?

RESPUESTA DEL DUEÑO:  *** «Crear usuarios de prueba nuevos en cesta-db-1.» ***

  Y la opcion decia, literalmente:
    «Uso `crea_usuario` para dar de alta 2-3 usuarios de prueba con nombres claros; NO TOCO TU CUENTA NI BORRO NADA.
     Es ADITIVO y REVERSIBLE (se pueden quitar despues con tu permiso).»
```

## 2. Y lo que hace falta, medido

```
EN PIE (medido hoy):
  cesta-api-1       Up (healthy)       <- la API de casa
  cesta-db-1        Up (healthy)       <- *** LA BASE DE CASA (5432) ***
  cesta-web-1       Up
  cesta-prueba-db   Up                 <- la de pruebas (5434)
  facylf-postgres   Up (healthy)       <- *** AJENO: NO SE TOCA ***

Y EL MECANISMO EXISTE:
  `plataforma/api/almacen.py:159`  def crea_usuario(usuario: str, nombre: str, clave: str) -> dict
  `plataforma/api/almacen.py:51`   class UsuarioRepetido(RuntimeError)     <- *** asi que es IDEMPOTENTE de hecho:
                                                                             si ya existe, LANZA, no duplica ***
  `plataforma/api/almacen.py:39`   ALTAS_POR_HORA = 10
  `plataforma/api/almacen.py:31`   MAX_INVITACIONES_VIVAS = 3

Y LO QUE NO HAY:  *** ningun script de semilla *** -- ni en `scripts/` ni en `tests/conftest.py`.
```

## 3. Y EL PROCEDIMIENTO, para ejecutarlo con contexto entero

```
PASO 1 -- VER, SIN ESCRIBIR:  cuantos usuarios hay ya, y con que nombres.
          *** Para no crear un «prueba1» al lado de un «prueba1» que ya existe. ***

PASO 2 -- COMPROBAR QUE `crea_usuario` NO TOCA NADA MAS:
          leer su cuerpo (`almacen.py:159-178`, ~20 lineas) y confirmar que **solo inserta en `usuario`**
          y **no escribe en `lista`, `lista_linea`, `entrada` ni `compra`.**

PASO 3 -- CREAR DOS O TRES, con nombres que se vean de lejos:
          *** el proyecto usa `propietario`/`usuario_id` en todo; unos nombres como
          `prueba-b13-1` / `prueba-b13-2` son **imposibles de confundir con una persona** y
          **se pueden borrar con un `DELETE` acotado** (y con tu permiso). ***

PASO 4 -- Y LOS CINCO RECORRIDOS, con esos usuarios:
          receta -> lista · plan -> lista · receta -> consumo · compra · diario.
          *** Y con las guardas de B13: movil/desktop, temas, zoom, y las cuatro condiciones de HTTP. ***

PASO 5 -- Y LA EVIDENCIA, con lo que B13 pide:
          capturas con **version de frontend/API + commit + catalogo + fecha + hash**, y
          **un manifiesto SIN DATOS PRIVADOS** -- *«sin commitear nutricion personal».*
```

> *** Y el paso 1 y el 2 son **la misma disciplina de todo el encargo**: *** **mirar antes de escribir**, y
> **comprobar que la funcion que se va a usar no toca mas de lo que se cree** -- *que es **exactamente** lo que
> `017_la_despensa.sql` dice de si mismo («no hay ninguna clave ajena a `compra`, ni ningun disparador que escriba
> aqui»). *
>
> *** Y el paso 3 usa **una propiedad del codigo**: *** *`crea_usuario` lanza `UsuarioRepetido` si el usuario ya
> existe -- *o sea: **crear dos veces no duplica**, *y **el propio codigo impide el dano que se teme.** *
> *** Octava forma de imposibilidad. ***

## 4. Y por que **no se ha ejecutado en esta ronda**

> *** Porque una escritura en la base de casa **no se hace con el contexto agotado**.***
>
> *** Y hay una razon concreta, no una precaucion vaga: *** *los pasos 1 y 2 **hay que hacerlos primero** -- *y
> **hacer el 3 sin el 1** es **exactamente** el error que esta sesion ha documentado nueve veces: **actuar antes de
> leer.** *
>
> *** Y el dueño ha autorizado **crear usuarios de prueba**, no **que se haga a ciegas**.***

## 5. Y B13 queda **listo para ejecutar**, no empezado a medias

```
  1) RUTAS Y COMPONENTES MONTADOS   *** HECHO *** -- `Suite` se sirve y `Nav` no; `APLICACIONES` tiene
                                    `/compra` · `/recetas` · `/calorias`; y `SUPERAPP-01` es el documento que las fija
  2) LOS CINCO RECORRIDOS           *** AUTORIZADO Y CON PROCEDIMIENTO *** -- y **es la siguiente accion**
  3) MOVIL/DESKTOP, TEMAS Y ZOOM    junto con el paso 4
  4) HTTP RETENIDA/ERROR/CANCELACION/LLEGADA TARDIA   junto con el paso 4
  5) CAPTURAS + MANIFIESTO          es el paso 5
  6) MEDIR PASOS plan->lista y receta->consumo        junto con el paso 4
  7) Y LA REGLA                     «no cerrar A09 entero con vacios unicamente»
```

> *** Y lo que esta ronda deja **no es trabajo hecho: es trabajo desbloqueado**, *** *con **los cinco pasos en orden**,
> **la comprobacion previa escrita**, y **la razon de cada uno**.*
>
> *** Que es lo unico honesto que se puede dejar cuando **la decision es de otro y el contexto es de uno**. ***
