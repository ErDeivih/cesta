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
USER cesta

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=4s --start-period=20s \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/salud').read()"

CMD ["uvicorn", "plataforma.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
