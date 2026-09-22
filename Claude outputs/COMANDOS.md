# Comandos para ejecutar en tu PC

Todos desde `F:\aprendizaje\scrap` en PowerShell. **En PowerShell la línea no se
parte con `\`** — si hace falta partirla, el continuador es el acento grave.

---

## 1. Lo primero: que el cambio de hoy esté bien

```powershell
uv run pytest -q
uv run ruff check .
```

Esperado: **308 en verde**. Aquí fallan 2 por un fichero de SQL que no copié al
contenedor; en tu PC deberían pasar las 310.

```powershell
uv run python -m projects.cesta.auditar_secciones
```

Esperado: `0` claves contradiciendo su rama, `0` hojas fuera de su rama, `0`
secciones vacías, y sólo **143 productos sin sección en Aldi** (sujetadores,
toallas, plantas: el bazar de Aldi, que no es de supermercado).

---

## 2. Rellenar las secciones sin esperar a mañana

Las pantallas de pasillos y de posición están vacías hasta que `seccion` llegue
a gold. Se llena solo en la ejecución de mañana, o ahora con:

```powershell
uv run python -m projects.cesta.pipeline
uv run python -m projects.cesta.emparejar
```

El pipeline tarda un par de minutos; `emparejar`, unos 15.

---

## 3. La comprobación que yo no puedo hacer: ¿nos falta catálogo?

Desde la nube no hay red hacia ningún supermercado (el proxy devuelve 403 en el
CONNECT), así que lo único que no he podido verificar es si estamos bajando
**todo lo que cada cadena publica**. Lo de dentro ya lo he comprobado y está
bien; esto compara contra la fuente.

```powershell
uv run python -m projects.cesta.auditar_recorrido
```

---

## 4. Eroski: seguir donde lo dejamos

La ficha de producto, que es lo que queda por mirar:

```powershell
uv run python -m projects.cesta.sondear_cadena eroski --guardar
```

Lo que busco en la salida: si la ficha trae **EAN, ingredientes y tabla
nutricional**. Si los trae, Eroski entra; si no, es una cadena de precios sin
nada con lo que emparejar y no compensa.

Pégame la salida tal cual.

---

## 5. Levantar la plataforma (lo único que falta para usarla)

```powershell
cd plataforma
copy .env.ejemplo .env
notepad .env          # cambiar CESTA_CLAVE_DB
.\arrancar.bat
.\arrancar.bat cuenta david "David"
.\arrancar.bat cuenta mama "Mamá"
```

Luego `http://localhost:8080` en el PC.

---

## 6. Si algo se rompe

```powershell
uv run python -m projects.cesta.resumen          # qué hay y qué falta
uv run python -m projects.cesta.auditar_crudo    # campos que bajamos y no usamos
type data\ejecuciones.log | Select-Object -Last 40
```
