# El vigilante de la ingesta, con programación propia

**07/11/2026.** Arregla el punto ciego del bloque 3: el vigilante vivía **al final de
`ejecutar.bat`**, así que si el Programador de tareas no lanzaba la recolección, el vigilante
tampoco se ejecutaba. Nadie avisaba del fallo más grave posible: que el día no empezara.

## 1. Qué se ha hecho

- **`ejecutar-vigilante.bat`** (nuevo): ejecuta `scripts/vigilar_ingesta --solo-fallos`, deja el
  informe en `data/avisos_ingesta.json`, escribe en `data/avisos_ingesta.log`, y si hay fallo crea
  `data/INGESTA-DETENIDA.txt` (visible en la raíz de `data/`) y refresca `metricas-cesta.json`
  para que el panel también lo vea.
- **`registrar-vigilante.ps1`** (nuevo): da de alta la tarea **«Cesta vigilante»**.
- **Tarea registrada** el 07/11/2026: diaria a las **06:30, 08:00, 14:00 y 20:00**, más un
  disparador **al iniciar sesión con 25 minutos de margen**, `StartWhenAvailable`,
  `MultipleInstances IgnoreNew`, límite de 30 minutos. Próxima ejecución comprobada:
  **07/11/2026 06:30**.
- **Segunda mirada:** el `.bat` no falla a la primera. Si el ordenador acaba de arrancar y la
  recolección está empezando, espera 5 minutos y vuelve a mirar. Solo entonces avisa. Así no
  convierte el arranque del PC en un falso «no ha arrancado».

## 2. Qué contesta, y qué no

El vigilante ya sabía distinguir (y sigue haciéndolo):

| Situación | Qué dice | Código con `--solo-fallos` |
|---|---|---|
| La pasada de hoy está en curso | `en_curso`, no es fallo | 0 |
| Hoy no hay pasada, o gold no se publicó | `sin_pasada` / `gold_atrasado` | 1 |
| Una pasada murió a medias | `pasada_a_medias` | 1 |
| Alcampo corto (vara del 17/10) | aviso, no fallo | 0 |
| Todo correcto | `ok` | 0 |

La diferencia con antes: ahora **la comprobación no depende de que la recolección haya
arrancado**. Si el Programador no lanza `ejecutar.bat`, la tarea «Cesta vigilante» se lanza igual
a las 06:30, 08:00, 14:00 o 20:00 (o al iniciar sesión) y encuentra `sin_pasada`. La de las 06:30
es la que hace que un día sin arranque se note a primera hora, no al final.

## 3. Cómo se comprueba

```powershell
Get-ScheduledTask -TaskName 'Cesta vigilante' | Get-ScheduledTaskInfo
Get-ScheduledTask -TaskName 'Cesta vigilante' | Select-Object -ExpandProperty Triggers
schtasks /Query /TN "Cesta vigilante" /V /FO LIST   # acción, usuario y disparadores
```

Lo que se vio al registrar:

- acción: `F:\Proyectos\cesta\ejecutar-vigilante.bat`;
- ejecutar como: `David`, solo cuando la sesión está iniciada;
- próxima ejecución: `07/11/2026 06:30`;
- estado: listo (habilitado).

Lanzarla a mano para probar sin esperar:

```powershell
Start-ScheduledTask -TaskName 'Cesta vigilante'
Get-Content data\avisos_ingesta.json
```

Si se lanza antes de que la recolección del día haya terminado, puede dejar un aviso **honesto**
(«aún no ha llegado»), no un fallo inventado: el `--solo-fallos` y el estado `en curso` están para
eso.

## 4. Qué pasa cuando avisa

- `data/avisos_ingesta.json` con `estado: "fallo"` y los códigos.
- `data/avisos_ingesta.log` con fecha y hora.
- `data/INGESTA-DETENIDA.txt` con el motivo y el comando para relanzar.
- `metricas-cesta.json` con el bloque `ingesta` actualizado (el panel de David lo lee).
- En el panel / la app, el estado de ingesta pasa a fallo.

No hay correo ni push: el aviso es local, en los ficheros que ya se miran. Si algún día se quiere
un canal externo, se añade sin cambiar la detección.

## 5. Límites, dichos

- La tarea corre **solo con la sesión iniciada** (igual que la recolección: el WAF de Alcampo
  necesita navegador visible). Si el PC está apagado y nadie inicia sesión, no hay ni recolección
  ni vigilante; `StartWhenAvailable` la recupera al siguiente inicio de sesión.
- El vigilante **no puede avisar de que él mismo no se ha ejecutado**. Para eso está el
  Programador (historial de la tarea) y el hecho de que el panel dejaría de actualizar
  `metricas-cesta.json`; se puede añadir un chequeo externo el día que haya servidor.
- La hora: 06:30, 08:00, 14:00 y 20:00. La de las 06:30 detecta el día que no arrancó a primera
  hora; la de las 08:00 es la segunda oportunidad; la de las 14:00 mira la ventana normal de
  publicación (el 6/11 publicó a las 12:34); la de las 20:00 recoge un arranque tardío que se
  quedó a medias. Si la recolección sigue en curso, el estado es «en curso» y no fallo.
- Registro: `Register-ScheduledTask` pidió administrador en esta sesión; se dio de alta con
  `schtasks /Create` (misma tarea, usuario actual) y luego se le añadieron los disparadores con
  `Set-ScheduledTask`. La tarea actual tiene **06:30, 08:00, 14:00, 20:00 e inicio de sesión**; el
  script `registrar-vigilante.ps1` deja exactamente esos cinco disparadores.
