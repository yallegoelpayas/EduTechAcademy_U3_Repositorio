"""CU-02 Control de asistencia."""
from datetime import date, datetime

from ..dominio.repositorios import ExpedienteRepository, GrupoRepository
from ..dominio.servicios import CalendarioDeDiasHabiles
from .puertos import ControlDeAcceso, UnitOfWork, exigirRol, transaccion


class AsistenciaService:
    def __init__(self, uow: UnitOfWork, expedientes: ExpedienteRepository, grupos: GrupoRepository,
                 acceso: ControlDeAcceso, calendario: CalendarioDeDiasHabiles):
        self.uow, self.expedientes, self.grupos = uow, expedientes, grupos
        self.acceso, self.calendario = acceso, calendario

    def registrarAsistencia(self, inscripcionId: str, sesion: int, presente: bool, usuarioId: str,
                            ahora: datetime) -> float:
        exigirRol(self.acceso, usuarioId, "Instructor", "LMS")
        with transaccion(self.uow):
            expediente = self.expedientes.obtener(inscripcionId)
            grupo = self.grupos.obtener(expediente.grupoId)
            expediente.registrarAsistencia(sesion, grupo.sesiones[sesion - 1], presente, ahora)  # INV-11
            self.expedientes.guardar(expediente)
        return expediente.porcentajeAsistencia(len(grupo.sesiones))

    def corregirAsistenciaExtemporanea(self, inscripcionId: str, sesion: int, presente: bool,
                                       justificacion: str, usuarioId: str, ahora: datetime) -> None:
        exigirRol(self.acceso, usuarioId, "ControlEscolar")
        with transaccion(self.uow):
            expediente = self.expedientes.obtener(inscripcionId)
            expediente.corregirAsistencia(sesion, presente, justificacion, ahora)   # INV-11
            self.expedientes.guardar(expediente)

    def justificarInasistencia(self, inscripcionId: str, sesion: int, presentadaEn: date,
                               usuarioId: str) -> bool:
        exigirRol(self.acceso, usuarioId, "ControlEscolar")
        with transaccion(self.uow):
            expediente = self.expedientes.obtener(inscripcionId)
            grupo = self.grupos.obtener(expediente.grupoId)
            limite = self.calendario.sumarDiasHabiles(grupo.sesiones[sesion - 1].date(), 5)
            justificada = expediente.justificarInasistencia(sesion, presentadaEn, limite)  # INV-13
            self.expedientes.guardar(expediente)
        return justificada
