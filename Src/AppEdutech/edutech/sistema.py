"""Ensambla las capas: crea la infraestructura y la inyecta en los Application Services."""
from .aplicacion.acta_service import ActaService
from .aplicacion.asistencia_service import AsistenciaService
from .aplicacion.calificacion_service import CalificacionService
from .aplicacion.certificado_service import CertificadoService
from .aplicacion.consultas import EstadoDePagoQuery, VerificacionPublicaService
from .aplicacion.inscripcion_service import InscripcionService
from .dominio.servicios import CalendarioDeDiasHabiles, ConsolidadorDeActa
from .infraestructura.adapters import (ControlDeAccesoAdapter, LmsAdapter, NotificacionGatewayAdapter,
                                       SistemaContableAdapter)
from .infraestructura.sql import (EstadoDePagoSqlReader, SqlActaRepository, SqlCertificadoRepository,
                                  SqlCursoRepository, SqlExpedienteRepository, SqlGrupoRepository,
                                  SqlInscripcionRepository, SqlUnitOfWork, VerificacionPublicaSqlReader, conectar)


class Sistema:
    def __init__(self, roles: dict[str, set[str]], ruta: str = ":memory:", inhabiles=None):
        c = self.conexion = conectar(ruta)
        uow = SqlUnitOfWork(c)
        self.cursos, self.grupos = SqlCursoRepository(c), SqlGrupoRepository(c)
        self.inscripciones, self.expedientes = SqlInscripcionRepository(c), SqlExpedienteRepository(c)
        self.actas, self.certificados = SqlActaRepository(c), SqlCertificadoRepository(c)
        self.notificaciones = NotificacionGatewayAdapter()
        acceso = ControlDeAccesoAdapter({**roles, LmsAdapter.USUARIO: {"LMS"}})
        calendario = CalendarioDeDiasHabiles(inhabiles)
        self.inscripcion = InscripcionService(uow, self.cursos, self.grupos, self.inscripciones,
                                              self.expedientes, self.notificaciones)
        self.asistencia = AsistenciaService(uow, self.expedientes, self.grupos, acceso, calendario)
        self.calificacion = CalificacionService(uow, self.expedientes, self.inscripciones, self.cursos)
        self.acta = ActaService(uow, self.actas, self.grupos, self.inscripciones, self.expedientes, self.cursos,
                                ConsolidadorDeActa(), calendario)
        self.certificado = CertificadoService(uow, self.certificados, self.actas, acceso, calendario)
        self.verificacion = VerificacionPublicaService(VerificacionPublicaSqlReader(c))
        self.estadoDePago = EstadoDePagoQuery(EstadoDePagoSqlReader(c))
        self.contable = SistemaContableAdapter(self.inscripcion)
        self.lms = LmsAdapter(self.asistencia)

    def __del__(self):
        self.conexion.close()
