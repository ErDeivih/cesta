# Encargo de continuación vigente · 13/10/2026

El Word `CESTA-ENCARGO-DEEPSEEK-2026-10-13.docx` es la copia para lectura y entrega.
Su fuente única es `../SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md`.
El bloque para sustituir el objetivo de DeepSeek está en `../SUPERAPP-GOAL-ACTUAL.md`;
el seguimiento corto, en `../SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md`.
Los encargos anteriores se conservan como históricos, no como objetivo activo.

## Verificación del entregable

- Generado con `scripts/exportar_encargo_word.cjs` y la dependencia documental `docx`.
- Validador OOXML de la skill Word: **All validations PASSED**, 172 párrafos.
- ZIP íntegro; XML legible; comprobados B00–B16, cinco recetas, cifras y límites.
- No hubo validación visual de paginación: la instancia de Word COM no arrancó
  (`CO_E_SERVER_EXEC_FAILURE`, 80080005); LibreOffice no estaba disponible.
  No se afirma que haya PDF/capturas ni que el layout se haya inspeccionado.

La investigación de referencias es documental, desde páginas oficiales. No se
ha decompilado una app comercial ni acreditado su mecanismo interno. El plan
incluye los estudios puntuales futuros con REA y sus límites de evidencia.

No se ha reactivado un bucle externo de DeepSeek automáticamente. Para hacerlo,
reemplazar allí su objetivo por el bloque del GOAL ACTUAL y reanudar desde sus controles.

## Regenerar

Con `docx` resoluble por Node (o NODE_PATH de las dependencias del entorno):

```powershell
node scripts/exportar_encargo_word.cjs docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md docs/entregables/CESTA-ENCARGO-DEEPSEEK-2026-10-13.docx
```

El renderizador opcional `scripts/renderizar_encargo_word.ps1` necesita Word COM
funcional. No reparar ni reinstalar Office solo para ejecutar este encargo.
