"""Value Objects: se definen por sus valores y validan sus propias reglas."""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from .errores import EvaluacionFueraDeRango, PonderacionInvalida, SobrecupoNoPermitido


class Modalidad(Enum):
    PRESENCIAL = "presencial"
    EN_LINEA = "en línea"

    @property
    def cupoMaximo(self) -> int:
        # INV-03: 25 presencial, 40 en línea (BRD, US-03).
        return 25 if self is Modalidad.PRESENCIAL else 40


@dataclass(frozen=True)
class Cupo:
    """INV-03: lugares disponibles; sobrecupo de hasta 10% solo con autorización de Administración."""
    maximo: int
    sobrecupoAutorizado: int = 0

    def __post_init__(self):
        if self.sobrecupoAutorizado < 0 or self.sobrecupoAutorizado > self.maximo // 10:
            raise SobrecupoNoPermitido(f"El sobrecupo máximo es {self.maximo // 10} lugares")

    @property
    def capacidad(self) -> int:
        return self.maximo + self.sobrecupoAutorizado


@dataclass(frozen=True)
class Ponderacion:
    """INV-01: suma 100. Por defecto 40% parciales, 40% proyecto final y 20% actividades."""
    parciales: int = 40
    proyecto: int = 40
    actividades: int = 20

    def __post_init__(self):
        if self.parciales + self.proyecto + self.actividades != 100:
            raise PonderacionInvalida("La ponderación debe sumar 100")

    def peso(self, tipo: str) -> int:
        return {"parcial": self.parciales, "proyecto": self.proyecto, "actividad": self.actividades}[tipo]


@dataclass(frozen=True)
class CriterioDeCertificacion:
    """INV-02 e INV-21: Regular (70 y 80%) u Oficial (80 y 90%)."""
    calificacionMinima: float
    asistenciaMinima: float

    @staticmethod
    def regular() -> "CriterioDeCertificacion":
        return CriterioDeCertificacion(70, 80)

    @staticmethod
    def oficial() -> "CriterioDeCertificacion":
        return CriterioDeCertificacion(80, 90)

    def evaluar(self, calificacion: float, asistencia: float) -> tuple[bool, str | None]:
        if calificacion < self.calificacionMinima:
            return False, "calificación"
        if asistencia < self.asistenciaMinima:
            return False, "asistencia"
        return True, None


@dataclass(frozen=True)
class PagoAcreditado:
    """Pago confirmado por el sistema contable (externo)."""
    monto: float
    fecha: date


@dataclass(frozen=True)
class Evaluacion:
    """INV-14: valor entre 0 y 100; guarda quién la capturó (INV-17)."""
    tipo: str          # parcial, proyecto o actividad
    valor: float
    instructorId: str

    def __post_init__(self):
        if self.tipo not in ("parcial", "proyecto", "actividad"):
            raise ValueError("Tipo de evaluación desconocido")
        if not 0 <= self.valor <= 100:
            raise EvaluacionFueraDeRango("La evaluación debe estar entre 0 y 100")


@dataclass(frozen=True)
class AsistenciaRegistrada:
    presente: bool
    registradaEn: datetime
    justificacion: str | None = None

    @staticmethod
    def acreditaEnLinea(porcentajeConexion: float, horasHastaVerGrabacion: float | None) -> bool:
        """INV-12: 60% de conexión en vivo o ver la grabación dentro de 72 horas."""
        return porcentajeConexion >= 60 or (horasHastaVerGrabacion is not None and horasHastaVerGrabacion <= 72)


@dataclass(frozen=True)
class LineaDeActa:
    inscripcionId: str
    estudiante: str
    calificacionFinal: float
    porcentajeAsistencia: float
    cumple: bool
    motivo: str | None
