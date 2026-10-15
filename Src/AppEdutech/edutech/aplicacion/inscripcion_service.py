"""CU-01 Gestión de inscripción y cupos."""
from dataclasses import dataclass
from datetime import date, datetime

from ..dominio.errores import SinCupo
from ..dominio.eventos import LugarOfrecidoAlSiguienteEnEspera
from ..dominio.expediente import ExpedienteAcademico
from ..dominio.inscripcion import Inscripcion
from ..dominio.repositorios import (CursoRepository, ExpedienteRepository, GrupoRepository,
                                    InscripcionRepository)
from ..dominio.valores import PagoAcreditado
from .puertos import NotificacionGateway, UnitOfWork, transaccion


@dataclass(frozen=True)
class SolicitarInscripcion:
    """Command (Etapa 6): intención de inscribirse a un grupo."""
    estudianteId: str
    grupoId: str
    datos: dict
    ahora: datetime


@dataclass(frozen=True)
class SolicitudRegistrada:
    inscripcionId: str
    estado: str
    monto: float
    fechaLimitePago: date


@dataclass(frozen=True)
class EnListaDeEspera:
    grupoId: str
    fechaHora: datetime


class InscripcionService:
    def __init__(self, uow: UnitOfWork, cursos: CursoRepository, grupos: GrupoRepository,
                 inscripciones: InscripcionRepository, expedientes: ExpedienteRepository,
                 notificaciones: NotificacionGateway):
        self.uow, self.cursos, self.grupos = uow, cursos, grupos
        self.inscripciones, self.expedientes, self.notificaciones = inscripciones, expedientes, notificaciones

    def solicitarInscripcion(self, cmd: SolicitarInscripcion) -> SolicitudRegistrada | EnListaDeEspera:
        with transaccion(self.uow):
            grupo = self.grupos.obtener(cmd.grupoId)
            curso = self.cursos.obtener(grupo.cursoId)
            inscripcionId = self.inscripciones.siguienteId()
            try:
                reservado = grupo.reservarLugar(inscripcionId)                  # INV-03
            except SinCupo:
                grupo.agregarAListaDeEspera(cmd.estudianteId, cmd.ahora)       # INV-04, US-04
                self.grupos.guardar(grupo)
                return EnListaDeEspera(grupo.grupoId, cmd.ahora)
            inscripcion = Inscripcion.preinscribir(inscripcionId, cmd.estudianteId, grupo.grupoId,
                                                   cmd.datos, curso.costo, reservado.fechaLimitePago)  # REG-01
            self.inscripciones.agregar(inscripcion)
            # El Expediente se crea con la Preinscripción porque un Preinscrito puede asistir (US-06).
            self.expedientes.guardar(ExpedienteAcademico(inscripcionId, curso.cursoId, grupo.grupoId))
            self.grupos.guardar(grupo)
        return SolicitudRegistrada(inscripcionId, inscripcion.estado.value, inscripcion.monto,
                                   inscripcion.fechaLimitePago)

    def acreditarPago(self, inscripcionId: str, monto: float, fecha: date):
        """Lo invoca el SistemaContableAdapter cuando el sistema contable notifica un pago."""
        with transaccion(self.uow):
            inscripcion = self.inscripciones.obtener(inscripcionId)
            evento = inscripcion.registrarPago(PagoAcreditado(monto, fecha))   # INV-06 a INV-08
            self.inscripciones.guardar(inscripcion)
        return evento

    def liberarPorPlazoVencido(self, inscripcionId: str, hoy: datetime) -> list:
        """SEQ-02: la Inscripción decide si venció; el Grupo libera y ofrece el lugar."""
        eventos = []
        with transaccion(self.uow):
            inscripcion = self.inscripciones.obtener(inscripcionId)
            vencido = inscripcion.vencerPlazo(hoy.date())                      # INV-09
            if vencido is None:
                return []
            grupo = self.grupos.obtener(inscripcion.grupoId)
            eventos = [vencido] + grupo.liberarLugar(inscripcionId, hoy)      # INV-04
            self.inscripciones.guardar(inscripcion)
            self.grupos.guardar(grupo)
        # Se notifica después de confirmar para no avisar de un lugar que no se liberó (ADR-02).
        for e in eventos:
            if isinstance(e, LugarOfrecidoAlSiguienteEnEspera):
                self.notificaciones.notificarLugarDisponible(e.estudianteId, e.vence)
        return eventos
