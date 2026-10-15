"""Domain Services: comportamientos que no pertenecen a una sola entidad."""
from datetime import date, timedelta

from .expediente import ExpedienteAcademico
from .valores import CriterioDeCertificacion, LineaDeActa, Ponderacion


class CalendarioDeDiasHabiles:
    """Calcula los plazos de 3, 5 y 10 días hábiles del BRD.

    Pendiente de validar: qué días inhábiles considera la escuela (aquí, fines de semana y la lista dada)."""

    def __init__(self, inhabiles: set[date] | None = None):
        self.inhabiles = inhabiles or set()

    def esHabil(self, dia: date) -> bool:
        return dia.weekday() < 5 and dia not in self.inhabiles

    def sumarDiasHabiles(self, fecha: date, dias: int) -> date:
        actual = fecha
        while dias > 0:
            actual += timedelta(days=1)
            if self.esHabil(actual):
                dias -= 1
        return actual


class ConsolidadorDeActa:
    """Arma las líneas del acta cruzando Expedientes y el Criterio del Curso (US-13, US-14)."""

    def consolidar(self, expedientes: list[tuple[ExpedienteAcademico, str]], criterio: CriterioDeCertificacion,
                   ponderacion: Ponderacion, totalSesiones: int) -> tuple[list[LineaDeActa], list[int]]:
        """Recibe (expediente, nombre del estudiante) de las inscripciones Inscrito (INV-20).

        Devuelve las líneas del acta y las sesiones que no tienen asistencia capturada (INV-19)."""
        lineas, sinAsistencia = [], set()
        for expediente, nombre in expedientes:
            sinAsistencia.update(expediente.sesionesSinRegistro(range(1, totalSesiones + 1)))
            calificacion = expediente.calificacionFinal(ponderacion)
            asistencia = expediente.porcentajeAsistencia(totalSesiones)
            cumple, motivo = criterio.evaluar(calificacion, asistencia)       # INV-21
            lineas.append(LineaDeActa(expediente.inscripcionId, nombre, calificacion, asistencia, cumple, motivo))
        return lineas, sorted(sinAsistencia)
