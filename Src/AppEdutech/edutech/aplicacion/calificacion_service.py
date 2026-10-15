"""CU-03 Actualización de calificaciones."""
from ..dominio.inscripcion import EstadoInscripcion
from ..dominio.repositorios import CursoRepository, ExpedienteRepository, InscripcionRepository
from .puertos import UnitOfWork, transaccion


class CalificacionService:
    def __init__(self, uow: UnitOfWork, expedientes: ExpedienteRepository, inscripciones: InscripcionRepository,
                 cursos: CursoRepository):
        self.uow, self.expedientes, self.inscripciones, self.cursos = uow, expedientes, inscripciones, cursos

    def capturarEvaluacion(self, inscripcionId: str, clave: str, tipo: str, valor: float,
                           instructorId: str) -> float:
        """Captura una evaluación y devuelve la Calificación Final recalculada."""
        with transaccion(self.uow):
            expediente = self.expedientes.obtener(inscripcionId)
            inscrito = self.inscripciones.obtener(inscripcionId).estado is EstadoInscripcion.INSCRITO
            expediente.capturarEvaluacion(clave, tipo, valor, instructorId, inscrito)   # INV-14, 16, 17
            self.expedientes.guardar(expediente)
            curso = self.cursos.obtener(expediente.cursoId)
        return expediente.calificacionFinal(curso.ponderacion)                         # INV-15
