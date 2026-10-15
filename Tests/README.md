# Pruebas

28 pruebas con `unittest` (biblioteca estándar), basadas en los escenarios Gherkin de las historias de usuario:

- `test_dominio.py`: invariantes de los Aggregates y Value Objects, sin base de datos (17 pruebas).
- `test_servicios.py`: casos de uso completos a través de la Service Layer con SQLite en memoria, incluida la reversión del Unit of Work (11 pruebas).

Ejecutar desde esta carpeta:

```
python -m unittest -v
```

La relación entre cada regla (INV-xx) y su prueba está en la sección 9.3 del informe.
