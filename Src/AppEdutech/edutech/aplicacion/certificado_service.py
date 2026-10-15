"""Emisión de certificados (US-15; sin caso de uso propio en la Etapa 1)."""
from datetime import date

from ..dominio.certificado import Certificado
from ..dominio.errores import CertificadoNoAutorizado
from ..dominio.repositorios import ActaRepository, CertificadoRepository
from ..dominio.servicios import CalendarioDeDiasHabiles
from .puertos import ControlDeAcceso, UnitOfWork, transaccion


class CertificadoService:
    def __init__(self, uow: UnitOfWork, certificados: CertificadoRepository, actas: ActaRepository,
                 acceso: ControlDeAcceso, calendario: CalendarioDeDiasHabiles):
        self.uow, self.certificados, self.actas = uow, certificados, actas
        self.acceso, self.calendario = acceso, calendario

    def emitirCertificado(self, grupoId: str, inscripcionId: str, usuarioId: str, hoy: date) -> Certificado:
        # D-06: el servicio comprueba el rol; el Certificado registra quién autorizó (INV-24).
        if not self.acceso.tieneRol(usuarioId, "CoordinacionAcademica"):
            raise CertificadoNoAutorizado("Solo Coordinación Académica autoriza la emisión")
        with transaccion(self.uow):
            acta = self.actas.obtener(grupoId)
            limite = self.calendario.sumarDiasHabiles(acta.fechaCierre or hoy, 10)          # INV-25
            certificado, _ = Certificado.emitir(acta, inscripcionId, usuarioId, hoy, limite)  # INV-23 a INV-25
            self.certificados.agregar(certificado)
        return certificado
