"""Aggregate Inscripción: decide cuándo el estudiante queda Inscrito y cuándo se libera el lugar."""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from .errores import DatosIncompletos
from .eventos import InscripcionFormalizada, PlazoDePagoVencido
from .valores import PagoAcreditado

DATOS_OBLIGATORIOS = ("nombre", "correo", "telefono")


class EstadoInscripcion(Enum):
    PREINSCRITO = "Preinscrito"
    INSCRITO = "Inscrito"
    LIBERADA = "Liberada"      # propuesta del equipo (US-06 solo dice que se libera el lugar)


@dataclass
class Inscripcion:
    inscripcionId: str
    estudianteId: str
    grupoId: str
    datos: dict
    monto: float
    fechaLimitePago: date
    estado: EstadoInscripcion = EstadoInscripcion.PREINSCRITO
    pagos: list[PagoAcreditado] = field(default_factory=list)
    folio: str | None = None
    prorrogaHasta: date | None = None

    @classmethod
    def preinscribir(cls, inscripcionId: str, estudianteId: str, grupoId: str, datos: dict,
                     monto: float, fechaLimitePago: date) -> "Inscripcion":
        # REG-01: la solicitud solo se registra con los datos obligatorios completos (US-04).
        faltantes = [d for d in DATOS_OBLIGATORIOS if not str(datos.get(d, "")).strip()]
        if faltantes:
            raise DatosIncompletos("Faltan datos: " + ", ".join(faltantes))
        return cls(inscripcionId, estudianteId, grupoId, dict(datos), monto, fechaLimitePago)

    @property
    def totalPagado(self) -> float:
        return sum(p.monto for p in self.pagos)

    @property
    def saldoPendiente(self) -> float:
        return max(self.monto - self.totalPagado, 0)

    def registrarPago(self, pago: PagoAcreditado) -> InscripcionFormalizada | None:
        self.pagos.append(pago)
        # INV-06 e INV-07: con el total o la primera parcialidad del 50% queda Inscrito; si no, es abono.
        if self.estado is EstadoInscripcion.PREINSCRITO and self.totalPagado >= self.monto * 0.5:
            self.estado = EstadoInscripcion.INSCRITO
            self.folio = f"INS-{self.inscripcionId}"   # INV-08: se genera una sola vez y es único
            return InscripcionFormalizada(self.inscripcionId, self.folio)
        return None

    def autorizarProrroga(self, hasta: date) -> None:
        """Administración puede aprobar prórrogas (INV-09)."""
        self.prorrogaHasta = hasta

    def vencerPlazo(self, hoy: date) -> PlazoDePagoVencido | None:
        # INV-09: 7 días naturales desde el inicio del curso sin pago acreditado.
        limite = max(self.fechaLimitePago, self.prorrogaHasta or self.fechaLimitePago)
        if self.estado is EstadoInscripcion.PREINSCRITO and hoy > limite:
            self.estado = EstadoInscripcion.LIBERADA   # el Expediente conserva las sesiones asistidas
            return PlazoDePagoVencido(self.inscripcionId, self.grupoId)
        return None
