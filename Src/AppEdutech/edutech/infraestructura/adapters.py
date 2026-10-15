"""Adapters hacia sistemas externos y servicios de apoyo."""
from datetime import date, datetime

from ..aplicacion.asistencia_service import AsistenciaService
from ..aplicacion.inscripcion_service import InscripcionService
from ..aplicacion.puertos import ControlDeAcceso, NotificacionGateway
from ..dominio.valores import AsistenciaRegistrada


class NotificacionGatewayAdapter(NotificacionGateway):
    """En el código base solo guarda los avisos; en producción enviaría correo o mensaje."""
    def __init__(self):
        self.enviadas: list[tuple[str, datetime]] = []

    def notificarLugarDisponible(self, estudianteId, vence):
        self.enviadas.append((estudianteId, vence))


class ControlDeAccesoAdapter(ControlDeAcceso):
    """Roles en memoria; en producción vendrían del sistema de autenticación de la escuela."""
    def __init__(self, roles: dict[str, set[str]]):
        self.roles = roles

    def tieneRol(self, usuarioId, rol):
        return rol in self.roles.get(usuarioId, set())


class SistemaContableAdapter:
    """El sistema contable notifica pagos acreditados (supuesto del BRD)."""
    def __init__(self, servicio: InscripcionService):
        self.servicio = servicio

    def pagoNotificado(self, inscripcionId: str, monto: float, fecha: date):
        return self.servicio.acreditarPago(inscripcionId, monto, fecha)


class LmsAdapter:
    """El LMS o la videoconferencia informa la conexión de cada participante (INV-12)."""
    USUARIO = "sistema-lms"

    def __init__(self, servicio: AsistenciaService):
        self.servicio = servicio

    def conexionReportada(self, inscripcionId: str, sesion: int, porcentajeConexion: float,
                          horasHastaVerGrabacion: float | None, ahora: datetime) -> float:
        presente = AsistenciaRegistrada.acreditaEnLinea(porcentajeConexion, horasHastaVerGrabacion)
        return self.servicio.registrarAsistencia(inscripcionId, sesion, presente, self.USUARIO, ahora)
