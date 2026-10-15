"""Aggregate Acta: consolida el desempeño del grupo y se cierra (INV-18 a INV-22)."""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from .errores import ActaAunNoPuedeCerrarse, ActaConSesionesSinAsistencia, ActaYaCerrada
from .eventos import ActaCerrada
from .valores import LineaDeActa


class EstadoActa(Enum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


@dataclass
class Acta:
    grupoId: str
    curso: str
    estado: EstadoActa = EstadoActa.ABIERTA
    lineas: list[LineaDeActa] = field(default_factory=list)
    fechaConclusion: date | None = None
    fechaCierre: date | None = None

    def cerrar(self, lineas: list[LineaDeActa], sesionesSinAsistencia: list[int], hoy: date,
               fechaPermitida: date, fechaConclusion: date) -> ActaCerrada:
        if self.estado is EstadoActa.CERRADA:
            raise ActaYaCerrada("El acta ya está cerrada")                       # INV-22
        if hoy < fechaPermitida:
            raise ActaAunNoPuedeCerrarse(f"El acta se cierra a partir del {fechaPermitida}")  # INV-18
        if sesionesSinAsistencia:
            raise ActaConSesionesSinAsistencia(f"Sesiones sin asistencia: {sesionesSinAsistencia}")  # INV-19
        self.lineas = list(lineas)        # INV-20 e INV-21: las arma el Consolidador de Acta
        self.estado = EstadoActa.CERRADA
        self.fechaCierre = hoy
        self.fechaConclusion = fechaConclusion
        return ActaCerrada(self.grupoId, hoy)

    def lineaDe(self, inscripcionId: str) -> LineaDeActa | None:
        return next((l for l in self.lineas if l.inscripcionId == inscripcionId), None)
