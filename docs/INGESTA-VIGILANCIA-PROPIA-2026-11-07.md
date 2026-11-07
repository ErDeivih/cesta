# El vigilante de la ingesta, con programación propia

**07/11/2026.** Arregla el punto ciego del bloque 3: el vigilante vivía **al final de
`ejecutar.bat`**, así que si el Programador de tareas no lanzaba la recolección, el vigilante
tampoco se ejecutaba. Nadie avisaba del fallo más grave posible: que el día no empezara.

## 1. Qué se ha hecho

- **`ejecutar-vigilante.bat`** (nuevo): ejecuta
  `scripts/vigilar_ingesta --solo-fallos --margen-hasta 08:00`, deja el informe en
  `data/avisos_ingesta.json`, escribe su salida en **`data/vigilante.log`** (separado de
  `ejecuciones.log`, que la recolección tiene abierto mientras corre) y, si hay fallo, crea
  `data/INGESTA-DETENIDA.txt` y refresca `metricas-cesta.json` para el panel.
- **`registrar-vigilante.ps1`** (nuevo): da de alta la tarea **«Cesta vigilante»**.
- **Tarea registrada** el 07/11/2026: diaria a las **08:00, 14:00 y 20:00**, más un disparador
  **al iniciar sesión con 25 minutos de margen**, `StartWhenAvailable`,
  `MultipleInstances IgnoreNew`, límite de 30 minutos.
- **Segunda mirada:** el `.bat` no falla a la primera. Si el ordenador acaba de arrancar y la
  recolección está empezando, espera 5 minutos y vuelve a mirar. Solo entonces avisa.

## 2. Margen de arranque: no se avisa antes de las 08:00

La ingesta se programa a las **06:00**. Un informe hecho antes de esa ventana (o justo al
arrancar el PC) no puede llamar «fallo» a que no haya corrido: sería un aviso prematuro. Por eso:

- `--margen-hasta 08:00` (dos horas desde la hora programada) hace que, si todavía no hay pasada,
  el motivo sea **`en_margen_arranque`** con gravedad `aviso`, no `sin_pasada`/`gold_atrasado`
  con gravedad `fallo`.
- Con `--solo-fallos` eso sale **0**: dentro del margen no hay alarma. El aviso queda escrito y
  visible, pero no convierte el día en fallido.
- Pasadas las 08:00, si sigue sin pasada y sin gold del día, sí es fallo y sale 1.
- El margen **no se aplica con `--fecha` histórica**: reconstruir otro día no debe quedar tapado
  por la hora de hoy.

Reproducción del problema que corrige: un test con datos de prueba a las **05:00** llamaba
`vigila()` y recibía `sin_pasada` como fallo. Ahora la prueba vive en
`tests/test_vigilar_ingesta.py::test_antes_del_margen_de_arranque_no_se_avisa_de_que_falte`:
a las 05:00 el estado es «aviso», a las 09:00 el mismo árbol es «fallo».

## 3. Qué contesta, y qué no

| Situación | Qué dice | Código con `--solo-fallos` |
|---|---|---|
| Antes de las 08:00 y sin pasada | `en_margen_arranque`, aviso | 0 |
| La pasada de hoy está en curso | `en_curso`, no es fallo | 0 |
| Después de las 08:00, sin pasada o gold sin publicar | `sin_pasada` / `gold_atrasado` | 1 |
| Una pasada murió a medias | `pasada_a_medias` | 1 |
| Alcampo corto (vara del 17/10) | aviso, no fallo | 0 |
| Todo correcto | `ok` | 0 |

La diferencia con antes: **la comprobación no depende de que la recolección haya arrancado**. Si
el Programador no lanza `ejecutar.bat`, la tarea «Cesta vigilante» se lanza igual a las 08:00,
14:00 o 20:00 (o al iniciar sesión) y encuentra `sin_pasada` cuando ya ha pasado el margen.

## 4. Cómo se comprueba

```powershell
Get-ScheduledTask -TaskName 'Cesta vigilante' | Get-ScheduledTaskInfo
Get-ScheduledTask -TaskName 'Cesta vigilante' | Select-Object -ExpandProperty Triggers
schtasks /Query /TN "Cesta vigilante" /V /FO LIST   # acción, usuario y disparadores
```

**Primera ejecución real de la tarea, verificada el 07/11/2026:**

- lanzada a las **11:48:59** (Windows recuperó la tarea al iniciar sesión), con la recolección de
  hoy en curso;
- resultado: **0**, como corresponde a un día «en curso»;
- escribió `data/vigilante.log` (1.628 bytes) y actualizó `data/avisos_ingesta.json` a
  `fecha: 2026-11-07`, `estado: "aviso"`, `en_curso: true`;
- en la primera pasada automática (11:03) el `.bat` **no pudo escribir** porque `ejecuciones.log`
  estaba abierto por la recolección; por eso el vigilante tiene ahora su propio
  `data/vigilante.log`. Ese fallo quedó detectado y corregido en esta misma ronda.

La próxima ejecución programada es **07/11/2026 14:00**. La primera con margen completo será la
del **08/11 a las 08:00** (si la ingesta no ha arrancado, avisará entonces, no antes).

Si se lanza a mano antes de las 08:00, el resultado será un aviso `en_margen_arranque`, no un
fallo.

## 5. Qué pasa cuando avisa

- `data/avisos_ingesta.json` con `estado: "fallo"` y los códigos.
- `data/avisos_ingesta.log` con fecha y hora.
- `data/INGESTA-DETENIDA.txt` con el motivo y el comando para relanzar.
- `metricas-cesta.json` con el bloque `ingesta` actualizado (el panel de David lo lee).
- En el panel / la app, el estado de ingesta pasa a fallo.

No hay correo ni push: el aviso es local, en los ficheros que ya se miran. Si algún día se quiere
un canal externo, se añade sin cambiar la detección.

## 6. Límites, dichos

- La tarea corre **solo con la sesión iniciada** (igual que la recolección: el WAF de Alcampo
  necesita navegador visible). Si el PC está apagado y nadie inicia sesión, no hay ni recolección
  ni vigilante; `StartWhenAvailable` la recupera al siguiente inicio de sesión.
- El vigilante **no puede avisar de que él mismo no se ha ejecutado**. Para eso está el
  Programador (historial de la tarea) y el hecho de que el panel dejaría de actualizar
  `metricas-cesta.json`; se puede añadir un chequeo externo el día que haya servidor.
- Las horas 08:00, 14:00 y 20:00: la primera ya respeta el margen de arranque; la de las 14:00
  mira la ventana normal de publicación (el 6/11 publicó a las 12:34); la de las 20:00 recoge un
  arranque tardío que se quedó a medias. Si la recolección sigue en curso, el estado es «en curso»
  y no fallo.
- Registro: `Register-ScheduledTask` pidió administrador en esta sesión; se dio de alta con
  `schtasks /Create` (misma tarea, usuario actual) y luego se le añadieron los disparadores con
  `Set-ScheduledTask`. La tarea actual tiene **08:00, 14:00, 20:00 e inicio de sesión**; el script
  `registrar-vigilante.ps1` deja exactamente esos cuatro disparadores.
