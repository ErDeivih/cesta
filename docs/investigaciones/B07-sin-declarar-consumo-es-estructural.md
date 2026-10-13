# B07 · **«Sin declarar consumo» es ESTRUCTURAL**: `cocina.py` **no importa el diario**

*(13 de octubre de 2026. **Sexta ronda de B07. Y la clausula de la cocina queda cerrada por los imports.**)*

## 1. Lo que hay: **tres imports, y ninguno es de dentro**

```python
core/cocina.py

  l30: from __future__ import annotations
  l32: import re
  l33: from dataclasses import dataclass, field
  l34: from datetime import datetime, timedelta, timezone
```

> *** Y eso es todo. *** *Ni `core.diario`, ni `core.despensa`, ni `plataforma.api`, ni nada del proyecto.*
>
> *** O sea: `cocina.py` es un modulo **puro**: **tres cosas de la biblioteca estandar**, y **cero dependencias
> del proyecto**.*
>
> *** Y por eso **no puede** declarar consumo: **no tiene con que.** ***

## 2. Y contesta la clausula de B07 **con la forma mas fuerte de todas**

```
B07 PIDE:  «Cocina recuperable, pasos/temporizadores y preparado/pendiente, SIN DECLARAR CONSUMO»
   -> *** y `cocina.py` no importa `diario`: NO HAY CAMINO. ***
```

> *** Y ya van **cinco formas de imposibilidad** en esta sesion, y esta es la mas limpia: ***
>
>   ```
>   1) `lista_linea.id uuid PRIMARY KEY`        -- la base IMPIDE la fila repetida
>   2) `diario.fuente_dato TEXT NOT NULL`        -- la base IMPIDE guardar sin origen
>   3) `importar_receta.FUENTES` VACIA           -- nada permitido hasta declararlo
>   4) `ON CONFLICT (id) DO UPDATE`              -- y sin fila duplicada posible
>   5) *** y `cocina.py` SIN IMPORTAR `diario`  -- NO HAY CAMINO A CONSUMO ***
>   ```
>
> *** Y la (5) es la mas fuerte de las cinco: **las otras cuatro son restricciones de la base o del codigo; esta es
> la AUSENCIA DE DEPENDENCIA** *** -- *o sea: **no es que este prohibido: es que no esta.***
>
> *** Y es **exactamente** lo que el docstring de `017_la_despensa.sql` decia de la compra: *** *«No hay ninguna
> clave ajena a `compra`, ni ningun disparador que escriba aqui»* -- *y ahi lo llamo **«la forma fuerte de una
> regla: no una promesa, una imposibilidad»**.*
>
> *** Ahora es **la sexta vez**, y con el mismo motivo: *** **comprar no es comer, y cocinar tampoco.** ***

## 3. Y el contraste con `despensa.py`, que era el paso (4) del metodo

**Los dos ficheros son hermanos -- «lo que hay en casa» y «lo que se esta haciendo» -- y los dos son puros:**

```
core/despensa.py   ->  su tabla (`017`) NO tiene clave ajena a `compra` ni disparador
core/cocina.py     ->  NO importa `diario`
```

> *** Los dos hermanos dicen lo mismo de la misma forma: *** **la regla no esta escrita en el codigo, esta en la
> AUSENCIA de algo** *-- *una clave ajena que no existe, y un import que no se hace.*
>
> *** Y esa es la respuesta del proyecto a la restriccion del propietario, *** **dos veces, y en los dos modulos
> que tratan con «lo que se hace con la comida»**.
>
> *** «Compra no es consumo» y «cocinar no es comer»: **la misma regla, y las dos como imposibilidad.** ***

## 4. Y B07, con seis rondas

```
  1) EL EDITOR DE RECETA    LOCALIZADO
  2) LA IMPORTACION         HECHO -- mecanismo, guardas de fuente, `razon_declarada`, y la previa
  3) EL PLAN                *** POR MIRAR ***
  4) LA COCINA              *** HECHO: *** `cocina.py` puro (3 imports de stdlib), el temporizador como
                            hora de fin, `Cocina` y `Temporizador`; y «sin declarar consumo» **por no
                            importar el diario**
  5) Y LA VERSION           CON ENSAYO
  6) Y LA ACEPTACION        «CINCO RECETAS CON DATOS ... y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS»
```

> *** Y queda **una**: el plan (varias comidas por dia, repetir/duplicar semana, raciones por ocurrencia). ***
> *Que **no es de este fichero** -- `cocina.py` **no sabe de planes**, y lo dice no importando nada.*
