"""Aggregate Curso: guarda el esquema de evaluación y el criterio de certificación."""
from dataclasses import dataclass, field

from .valores import CriterioDeCertificacion, Modalidad, Ponderacion


@dataclass
class Curso:
    cursoId: str
    nombre: str
    modalidad: Modalidad
    costo: float
    ponderacion: Ponderacion = field(default_factory=Ponderacion)          # INV-01
    criterio: CriterioDeCertificacion = field(default_factory=CriterioDeCertificacion.regular)  # INV-02
