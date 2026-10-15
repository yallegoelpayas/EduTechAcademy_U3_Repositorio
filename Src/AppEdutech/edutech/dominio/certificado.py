"""Aggregate Certificado: se emite solo con acta cerrada, estudiante que cumple y autorización."""
from dataclasses import dataclass
from datetime import date

from .acta import Acta, EstadoActa
from .errores import CertificadoNoAutorizado, NoCumpleCriterios
from .eventos import CertificadoEmitido


@dataclass
class Certificado:
    folio: str
    inscripcionId: str
    titular: str
    curso: str
    fechaConclusion: date
    autorizadoPor: str
    fechaEmision: date
    dentroDePlazo: bool
    vigencia: str = "Vigente"     # pendiente de validar: la U2 no define cuándo deja de ser vigente

    @property
    def codigoQr(self) -> str:
        return f"https://edutech.example/verificar/{self.folio}"

    @classmethod
    def emitir(cls, acta: Acta, inscripcionId: str, autorizadoPor: str | None, hoy: date,
               limitePublicacion: date) -> tuple["Certificado", CertificadoEmitido]:
        linea = acta.lineaDe(inscripcionId)
        # INV-23: acta cerrada y estudiante que cumple.
        if acta.estado is not EstadoActa.CERRADA or linea is None or not linea.cumple:
            raise NoCumpleCriterios("Solo se emite con el acta cerrada y el estudiante en Cumple criterios")
        # INV-24: autorización de Coordinación Académica, registrada con usuario y fecha.
        if not autorizadoPor:
            raise CertificadoNoAutorizado("Falta la autorización de Coordinación Académica")
        folio = f"CERT-{inscripcionId}"   # INV-25: único (una inscripción, un certificado)
        cert = cls(folio, inscripcionId, linea.estudiante, acta.curso, acta.fechaConclusion,
                   autorizadoPor, hoy, hoy <= limitePublicacion)   # INV-25: 10 días hábiles tras el cierre
        return cert, CertificadoEmitido(folio, inscripcionId)
