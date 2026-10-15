# Código base

Código mínimo en Python 3.10+ que representa la arquitectura propuesta. Solo usa la biblioteca estándar (SQLite incluido); no hay que instalar nada.

```
Src/
├── demo.py                      recorrido completo de CU-01 a CU-05
└── edutech/
    ├── dominio/                 Aggregates, Value Objects, Domain Services, eventos, errores e interfaces de Repository
    ├── aplicacion/              Application Services, Commands y Queries, y puertos (UnitOfWork, NotificacionGateway…)
    ├── infraestructura/         SQLite (repositorios, Unit of Work, modelos de lectura) y adapters externos
    └── sistema.py               ensambla las capas (inyección de dependencias)
```

La dependencia va hacia adentro: `infraestructura → aplicacion → dominio`. El dominio no importa nada de las otras capas.

Los nombres de clases y métodos son los mismos del diagrama de clases (carpeta `Diagramas`) y de los diagramas de secuencia. Por eso los métodos usan camelCase en lugar del estilo habitual de Python.

**Simplificación:** cada Aggregate se guarda serializado en una columna; las columnas que usan los modelos de lectura (estado de pago y verificación pública) se guardan aparte.

Ejecutar la demostración desde la raíz del repositorio:

```
cd Src && python demo.py
```
