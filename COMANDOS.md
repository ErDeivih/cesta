# Comandos para ejecutar en tu PC

Desde `F:\Proyectos\cesta` en PowerShell. **En PowerShell la línea no se parte
con `\`** — el continuador es el acento grave.

---

## 1. Comprobar que todo está sano

```powershell
uv run pytest -q
uv run ruff check .
```

Esperado: **342 en verde**.

> Hasta el 21 de septiembre este comando era **destructivo**: una prueba del
> colector de Carrefour llamaba a `main()`, `main()` daba el día por bueno y
> escribía su bronze — el de verdad. Reemplazaba los 16.560 productos del día
> por 199 de mentira. Ya no puede pasar: bajo `pytest`, escribir dentro de
> `data/` revienta con `EscrituraDePrueba`. Si lo ejecutaste ese día antes del
> arreglo, mira que `data\bronze\fuente=carrefour\fecha=2026-09-21` pese algo
> más de 1 MB y no 30 KB.

---

## 2. La comprobación contra la web, cuando quieras verla entera

Ya corre sola al final de cada ejecución con 8 productos por cadena. A mano y
con más muestra:

```powershell
uv run python -m projects.cesta.verificar_precios --por-cadena 25
```

Dice, por cadena, cuántos de los precios que publicamos aparecen en la página
del supermercado. Distingue `no aparece` (el dato) de `404` (el enlace), de
`sin precio` (agotado o con login) y de `no se pudo` (la red).

---

## 3. Las secciones, si quieres revisarlas a mano

```powershell
uv run python -m projects.cesta.auditar_secciones
```

También corre sola cada día, y **aplica** las categorías nuevas cuya sección
hereda de su propio padre. Las dudosas las deja escritas en pantalla para que
las pongas tú.

---

## 4. Eroski: lo único que queda pendiente y necesita tu PC

```powershell
uv run python -m projects.cesta.sondear_cadena eroski --guardar
```

Busco en la salida si la ficha trae **EAN, ingredientes y tabla nutricional**.
Si los trae, Eroski entra; si no, es una cadena de precios sin nada con lo que
emparejar y no compensa. Pégame la salida tal cual.

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

Luego `http://localhost:8080`.

---

## 6. Por qué se cortó la ejecución de las 6:18 del 21

Se murió a las 9:31 sin dejar traza. No fue el límite de 4 horas (llevaba
3 h 13). El historial de la tarea lo dice:

```powershell
Get-ScheduledTaskInfo -TaskName "Cesta"
Get-WinEvent -LogName Microsoft-Windows-TaskScheduler/Operational -MaxEvents 40 |
  Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-24) } |
  Format-Table TimeCreated, Id, Message -Wrap
```

Ya no puede pasar en silencio: la ejecución deja una marca al empezar que sólo
se borra al terminar entera, y la siguiente avisa si se la encuentra.

---

## 7. Si algo va mal

```powershell
uv run python -m projects.cesta.resumen          # qué hay y qué falta
uv run python -m projects.cesta.auditar_crudo    # campos que bajamos y no usamos
type data\ejecuciones.log | Select-Object -Last 60
```
