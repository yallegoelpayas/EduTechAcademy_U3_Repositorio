"""Infraestructura SQL (SQLite de la biblioteca estándar).

Simplificación para el código base: cada Aggregate se guarda serializado en una columna `datos`;
las columnas que necesitan los modelos de lectura se guardan aparte para no tocar el dominio al consultar."""
import pickle
import sqlite3

from ..aplicacion.puertos import (EstadoDePagoDto, EstadoDePagoReader, UnitOfWork, VerificacionPublicaDto,
                                  VerificacionPublicaReader)
from ..dominio.errores import NoEncontrado
from ..dominio.repositorios import (ActaRepository, CertificadoRepository, CursoRepository,
                                    ExpedienteRepository, GrupoRepository, InscripcionRepository)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cursos (id TEXT PRIMARY KEY, datos BLOB);
CREATE TABLE IF NOT EXISTS grupos (id TEXT PRIMARY KEY, datos BLOB);
CREATE TABLE IF NOT EXISTS inscripciones (id TEXT PRIMARY KEY, grupo TEXT, estado TEXT, saldo REAL,
                                          fecha_limite TEXT, datos BLOB);
CREATE TABLE IF NOT EXISTS expedientes (id TEXT PRIMARY KEY, datos BLOB);
CREATE TABLE IF NOT EXISTS actas (id TEXT PRIMARY KEY, datos BLOB);
CREATE TABLE IF NOT EXISTS certificados (folio TEXT PRIMARY KEY, inscripcion TEXT UNIQUE, datos BLOB);
CREATE TABLE IF NOT EXISTS verificacion_publica (folio TEXT PRIMARY KEY, titular TEXT, curso TEXT,
                                                 fecha_conclusion TEXT, vigencia TEXT);
"""


def conectar(ruta: str = ":memory:") -> sqlite3.Connection:
    conexion = sqlite3.connect(ruta, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
    conexion.executescript(ESQUEMA)
    return conexion


class SqlUnitOfWork(UnitOfWork):
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def iniciar(self) -> None:
        self.conexion.execute("BEGIN")

    def confirmar(self) -> None:
        self.conexion.execute("COMMIT")

    def cancelar(self) -> None:
        self.conexion.execute("ROLLBACK")


class _SqlBase:
    tabla = ""

    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def _obtener(self, clave: str):
        fila = self.conexion.execute(f"SELECT datos FROM {self.tabla} WHERE id = ?", (clave,)).fetchone()
        if fila is None:
            raise NoEncontrado(f"No existe {clave} en {self.tabla}")
        return pickle.loads(fila[0])

    def _guardar(self, clave: str, objeto) -> None:
        self.conexion.execute(f"INSERT OR REPLACE INTO {self.tabla} (id, datos) VALUES (?, ?)",
                              (clave, pickle.dumps(objeto)))


class SqlCursoRepository(_SqlBase, CursoRepository):
    tabla = "cursos"
    def obtener(self, cursoId): return self._obtener(cursoId)
    def guardar(self, curso): self._guardar(curso.cursoId, curso)


class SqlGrupoRepository(_SqlBase, GrupoRepository):
    tabla = "grupos"
    def obtener(self, grupoId): return self._obtener(grupoId)
    def guardar(self, grupo): self._guardar(grupo.grupoId, grupo)


class SqlInscripcionRepository(_SqlBase, InscripcionRepository):
    tabla = "inscripciones"

    def obtener(self, inscripcionId): return self._obtener(inscripcionId)

    def agregar(self, inscripcion): self.guardar(inscripcion)

    def guardar(self, i):
        self.conexion.execute(
            "INSERT OR REPLACE INTO inscripciones (id, grupo, estado, saldo, fecha_limite, datos) VALUES (?,?,?,?,?,?)",
            (i.inscripcionId, i.grupoId, i.estado.value, i.saldoPendiente, i.fechaLimitePago.isoformat(),
             pickle.dumps(i)))

    def delGrupo(self, grupoId):
        filas = self.conexion.execute("SELECT datos FROM inscripciones WHERE grupo = ? ORDER BY id", (grupoId,))
        return [pickle.loads(f[0]) for f in filas]

    def siguienteId(self):
        total = self.conexion.execute("SELECT COUNT(*) FROM inscripciones").fetchone()[0]
        return f"{total + 1:05d}"


class SqlExpedienteRepository(_SqlBase, ExpedienteRepository):
    tabla = "expedientes"
    def obtener(self, inscripcionId): return self._obtener(inscripcionId)
    def guardar(self, expediente): self._guardar(expediente.inscripcionId, expediente)


class SqlActaRepository(_SqlBase, ActaRepository):
    tabla = "actas"
    def obtener(self, grupoId): return self._obtener(grupoId)
    def guardar(self, acta): self._guardar(acta.grupoId, acta)


class SqlCertificadoRepository(CertificadoRepository):
    def __init__(self, conexion):
        self.conexion = conexion

    def agregar(self, c):
        # La restricción UNIQUE refuerza INV-25 (un folio único por inscripción).
        self.conexion.execute("INSERT INTO certificados (folio, inscripcion, datos) VALUES (?,?,?)",
                              (c.folio, c.inscripcionId, pickle.dumps(c)))
        # La proyección de la verificación pública se actualiza en la misma transacción (ADR-03).
        self.conexion.execute("INSERT INTO verificacion_publica VALUES (?,?,?,?,?)",
                              (c.folio, c.titular, c.curso, c.fechaConclusion.isoformat(), c.vigencia))


class VerificacionPublicaSqlReader(VerificacionPublicaReader):
    def __init__(self, conexion):
        self.conexion = conexion

    def consultar(self, folio):
        from datetime import date
        fila = self.conexion.execute(
            "SELECT titular, curso, fecha_conclusion, vigencia FROM verificacion_publica WHERE folio = ?",
            (folio,)).fetchone()
        return VerificacionPublicaDto(fila[0], fila[1], date.fromisoformat(fila[2]), fila[3]) if fila else None


class EstadoDePagoSqlReader(EstadoDePagoReader):
    def __init__(self, conexion):
        self.conexion = conexion

    def consultar(self, inscripcionId):
        from datetime import date
        fila = self.conexion.execute("SELECT estado, saldo, fecha_limite FROM inscripciones WHERE id = ?",
                                     (inscripcionId,)).fetchone()
        return EstadoDePagoDto(fila[0], fila[1], date.fromisoformat(fila[2])) if fila else None
