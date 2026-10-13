# B16 · **«Casa frente a publico», re-verificado ahora mismo**: la API sigue sin publicarse

*(2026-10-14, ~03:00. **Y es la afirmacion mas importante del dictamen, y se comprueba en un comando.**)*

## 1. La seccion del dictamen, y su conclusion

```
`docs/investigaciones/B16-dictamen-por-capacidad.md:41-53` *** ## Casa frente a publico ***
  *** «LO PUBLICADO SON CUATRO PUERTOS DE LOOPBACK: `127.0.0.1:5432` · `:5434` · `:8080` *** *
  *** y la API (`cesta-api-1:8000`) NO se publica al host -- solo en la red interna de Docker *** *
  *** y su `/openapi.json` responde `{"detail":"Not Found"}` *** *
  *y `Ajustes.tsx` le dice al usuario: *** «los datos viven en el ordenador de casa y no salen de ahi» *** *
  *y el material de aprendizaje: *** `test_el_sitio_no_pide_nada_por_red` ·
  `test_nada_en_linea_porque_el_csp_de_caddy_lo_prohibe` *** *

  *** «O sea: *** *** USABLE EN CASA, SI. DESPLEGABLE PARA PUBLICO, NO. *** ***» *
  *** «*Y no es una carencia: es lo que el encargo pide -- «no despliegues publicamente ni abras puertos»
     -- *y esta medido.*» *** *
```

## 2. *** Y la verificacion, hecha ahora ***

```
$ docker ps --format "{{.Names}}  {{.Ports}}"
  *** cesta-api-1      8000/tcp ***                     *** <- SIN `127.0.0.1:` => NO PUBLICADO ***
  *** cesta-prueba-db  127.0.0.1:5434->5432/tcp ***     *-- la base de pruebas*
  *** cesta-web-1      80/tcp, 443/tcp, 2019/tcp, 443/udp, *** 127.0.0.1:8080->8080/tcp *** *
  *** cesta-db-1       127.0.0.1:5432->5432/tcp ***     *-- la de casa*
  *** facylf-postgres  127.0.0.1:5433->5432/tcp ***     *** <- EL AJENO, y NO SE TOCA *** *

$ `http://127.0.0.1:8080/openapi.json` -> *** 200 *** `<!doctype html>` *
$ `http://127.0.0.1:8000/openapi.json` -> *** no responde desde el host *** *
```

> *** O sea: ***
> ```
> *** 1) LA API NO ESTA PUBLICADA ***  *-- *y **se ve en la propia salida de `docker ps`: *
>    *** `8000/tcp` SIN el prefijo `127.0.0.1:` *** *-- *y **eso, en Docker, es «no hay mapeo al host».** *
> *** 2) Y la web (`:8080`) SI responde ***  *-- *y **devuelve el HTML de la SPA**, *no el openapi: *
>    *** *una SPA sirve su `index` para cualquier ruta, y eso es correcto.** *
> *** 3) Y `:8000` desde el host ***  *** NO RESPONDE *** *-- *que es **la prueba directa** de que no
>    esta publicado.* *
> *** 4) y `facylf-postgres` sigue ahi, en `127.0.0.1:5433` ***  *** y NO SE HA TOCADO. *** *
> ```

## 3. *** Y el matiz del `/openapi.json`, que conviene aclarar ***

> *** El dictamen dice: *** *** «y su `/openapi.json` responde `{"detail":"Not Found"}`» *** *-- *y **«su»
> es *el de la API.** *
>
> *** Y **yo probe el de la WEB**, *y **da `200` con el HTML de la SPA** -- *y **no es una contradiccion**: *
> ```
> *** el de la WEB (`:8080`) ***  -> *** Caddy sirve el `index` de la SPA para cualquier ruta *** *
> *** el de la API (`:8000`) ***  -> *** y responde `Not Found` *** *-- *porque **las rutas de docs
>    estan desactivadas** *-- *y **se mide DESDE DENTRO**, *porque **desde el host no hay a quien preguntar.** *
> ```
>
> *** -> o sea: *** *** **las dos frases son verdad, y describen dos puertas distintas**, *y **la de la API
> es la que importa**: *su openapi **no existe**, *y **su puerto no se publica.** *

## 4. Y el estado de B16, con **su afirmacion mas importante re-verificada**

```
*** B16 · «dictamen local frente a publico» ***
  *** la conclusion ***    -> *** «USABLE EN CASA, SI. DESPLEGABLE PARA PUBLICO, NO.» *** *
  *** y sus pruebas ***    -> *** los puertos de `docker ps`, *la API sin mapeo, *el `/openapi.json`, *
                              *`Ajustes.tsx` («no salen de ahi»), *y **los dos ensayos del material.** *
  *** y re-verificado ***  -> *** hoy: `cesta-api-1  8000/tcp` SIN `127.0.0.1:`, y `:8000` no responde *** ✓
  *** y lo ajeno ***       -> *** `facylf-postgres` en `127.0.0.1:5433`, SIN TOCAR *** ✓
```

> *** Y **el encargo pedia exactamente esto**: *** *** «entrega *** DICTAMEN LOCAL FRENTE A PUBLICO ***» --
> *y **esta**, *con su conclusion, *sus pruebas, *y **su re-verificacion.** *
