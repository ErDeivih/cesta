# La API. El scraper NO va aqui: necesita Windows y un Chrome de verdad para el
# WAF de Alcampo, y meterlo en un contenedor rompe lo que hoy funciona.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115" "uvicorn[standard]>=0.30" "duckdb>=1.0" \
    "psycopg[binary,pool]>=3.2" "argon2-cffi>=23" "pydantic>=2.7"

COPY core/ /app/core/
COPY plataforma/ /app/plataforma/

# El contenedor no escribe en gold nunca: se monta en solo lectura desde fuera.
ENV CESTA_GOLD=/datos/gold

RUN useradd -r -u 10001 cesta && chown -R cesta /app
# **Y el arranque, que adopta el volumen antes de bajar de privilegios.**
# *El `chown -R cesta /app` de arriba **no llega a `/app/data`**: *el volumen **se monta
# despues**, y el montaje tapa el directorio.* *Asi que **un volumen nuevo nace de `root`**,
# y la API -- que corre como `cesta` -- **no puede escribir**.* *El sintoma es
# «readonly database», que manda a mirar el disco, *y la causa son los permisos.*
# *Los motivos enteros, en `plataforma/entrar-api.sh`.*
RUN chmod +x /app/plataforma/entrar-api.sh
# *Y por eso **no hay `USER cesta` aqui**: *el `chown` necesita `root`, *y el guion **baja a
# `cesta` el mismo** antes de arrancar la API.* *Si el `chown` falla, **se para** en vez de
# seguir como `root`.*
ENTRYPOINT ["/app/plataforma/entrar-api.sh"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=4s --start-period=20s \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/salud').read()"

CMD ["uvicorn", "plataforma.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
