#!/bin/sh
# =============================================================================
#  El arranque de la API: **adopta su volumen, y despues baja de privilegios.**
#
#  **Por que existe, medido el 14/10/2026.** *La API se reconstruyo, arranco `(healthy)`,
#  y **«Recetas» dejo de poder guardar**: *crear una receta daba **500**, y el log decia:*
#
#      *** sqlite3.OperationalError: attempt to write a readonly database ***
#
#  *Y **no era el disco ni el montaje**: *`/app/data` estaba montado `rw`.* *Era que*
#  **el directorio y el fichero eran de `root`** *(los creo el contenedor viejo, que corria
#  como `root`)*, *y el contenedor nuevo **corre como `cesta` (uid 10001)***, *asi que **no
#  podia escribir**.*
#
#  **Y la causa de fondo no es un accidente**: *el `chown -R cesta /app` del `Dockerfile`
#  **no llega al volumen*** -- *porque el volumen **se monta despues**, y el montaje
#  **tapa** `/app/data`.* *Asi que **un volumen nuevo siempre nace de `root`**, *y hay que
#  adoptarlo **en cada arranque**.*
#
#  *Y el proyecto **ya lo sabia**, y lo tenia escrito como **paso a mano*** --
#  `plataforma/docker-compose.yml:150`:*
#
#      # docker run --rm -v scrap_datos_api:/de -v ...:/a alpine cp -a /de/. /a/
#
#  *** Y un paso a mano es un paso que en un despliegue limpio nadie da *** *-- *y el sintoma
#  no dice «permisos»: *dice **«readonly database»**, que manda a mirar el disco.* *
#
#  **Lo que hace este guion, y en este orden:**
#
#    1. *Si arranca como `root`* -- *que es lo unico que puede hacer un `chown`* --,
#       **adopta `/app/data`** para `cesta`.
#    2. *Y **baja a `cesta` inmediatamente**, con `setpriv`* -- *que viene en `util-linux`,
#       ya presente en `python:3.12-slim`, *asi que **no hay dependencia nueva**.* *
#    3. *Si algo del paso 1 falla, **se dice y se para***: *seguir como `root` seria
#       **peor que fallar**, porque la API entera quedaria corriendo con privilegios.*
#
#  *Y si ya arranca como `cesta`, no hace nada: **es el caso de `docker run` sin `root`**,
#  y ahi el volumen tiene que venir adoptado de fuera.*
# =============================================================================
set -e

if [ "$(id -u)" = "0" ]; then
    if [ -d /app/data ]; then
        if ! chown -R cesta:cesta /app/data 2>/dev/null; then
            echo "No se pudo adoptar /app/data: la API no puede escribir el recetario ni el diario." >&2
            echo "Y NO se arranca como root para taparlo: eso seria peor que fallar." >&2
            exit 1
        fi
    fi
    # *Y se baja de privilegios **antes** de arrancar nada.*
    exec setpriv --reuid=cesta --regid=cesta --init-groups "$@"
fi

# *Ya venia sin privilegios: se respeta y se arranca tal cual.*
exec "$@"
