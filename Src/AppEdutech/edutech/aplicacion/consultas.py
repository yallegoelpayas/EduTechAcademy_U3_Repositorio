"""Queries (Etapa 6): devuelven modelos de lectura, no Aggregates."""
from ..dominio.errores import NoEncontrado
from .puertos import EstadoDePagoDto, EstadoDePagoReader, VerificacionPublicaDto, VerificacionPublicaReader


class VerificacionPublicaService:
    """CU-05: sin credenciales, por folio o código QR (ADR-03)."""

    def __init__(self, reader: VerificacionPublicaReader):
        self.reader = reader

    def consultarCertificado(self, folioOQr: str) -> VerificacionPublicaDto:
        folio = folioOQr.rstrip("/").split("/")[-1]      # el QR lleva una URL que termina en el folio
        dto = self.reader.consultar(folio)
        if dto is None:
            raise NoEncontrado("No existe un certificado con ese folio")
        return dto


class EstadoDePagoQuery:
    """US-06: el estudiante consulta su saldo pendiente y la fecha límite."""

    def __init__(self, reader: EstadoDePagoReader):
        self.reader = reader

    def consultarEstadoDePago(self, inscripcionId: str) -> EstadoDePagoDto:
        dto = self.reader.consultar(inscripcionId)
        if dto is None:
            raise NoEncontrado("No existe la inscripción")
        return dto
