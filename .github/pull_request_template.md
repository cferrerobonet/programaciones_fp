## Qué cambia y por qué

<!-- Una o dos frases para quien usa la app y, si aplica, el ID de docs/PENDIENTE.md -->

## Versión

- [ ] `pyproject.toml` y `src/programaciones/__init__.py` con la misma versión (o «sin versión: no se publica»)
- [ ] Entrada en `CHANGELOG.md`

## Pruebas

- [ ] `scripts/qa.sh todo` en verde
- [ ] Test nuevo o ajustado; comprobado que **falla al revertir** el cambio
- [ ] Si toca el documento generado: render del PDF revisado y `-m referencias` en local

## Repositorio público

- [ ] Ninguna programación real, `.docx`, PDF ni dato personal en el diff (`git diff --name-only main`)
- [ ] Ningún dato del servidor de correo (ADR-016)

## Impacto documental

<!-- PRD, TRD, DESIGN, DOCUMENTO_GENERADO, MODELO_DE_DATOS, OPERACIONES… o «sin impacto documental» -->
