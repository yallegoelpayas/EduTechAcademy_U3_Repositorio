"""Domain Events: hechos del negocio que ya ocurrieron (tabla de eventos de la Etapa 3)."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class LugarReservado:
    grupoId: str
    inscripcionId: str
    fechaLimitePago: date


@dataclass(frozen=True)
class EstudianteAgregadoAListaDeEspera:
    grupoId: str
    estudianteId: str
    fechaHora: datetime


@dataclass(frozen=True)
class InscripcionFormalizada:
    inscripcionId: str
    folio: str


@dataclass(frozen=True)
class PlazoDePagoVencido:
    inscripcionId: str
    grupoId: str


@dataclass(frozen=True)
class LugarLiberado:
    grupoId: str
    inscripcionId: str


@dataclass(frozen=True)
class LugarOfrecidoAlSiguienteEnEspera:
    grupoId: str
    estudianteId: str
    vence: datetime


@dataclass(frozen=True)
class ActaCerrada:
    grupoId: str
    fechaCierre: date


@dataclass(frozen=True)
class CertificadoEmitido:
    folio: str
    inscripcionId: str
