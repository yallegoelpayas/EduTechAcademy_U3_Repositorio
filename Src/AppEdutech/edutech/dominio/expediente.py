"""Aggregate Expediente Académico: asistencia y evaluaciones de una Inscripción."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .errores import (ActaYaCerrada, EdicionBloqueada, EvaluacionDeOtroInstructor, InscripcionNoInscrita,
                      JustificacionInvalida)
from .valores import AsistenciaRegistrada, Evaluacion, Ponderacion

PLAZO_INSTRUCTOR = timedelta(hours=48)
JUSTIFICACIONES_PERMITIDAS = 2


@dataclass
class ExpedienteAcademico:
    inscripcionId: str
    cursoId: str
    grupoId: str
    asistencias: dict[int, AsistenciaRegistrada] = field(default_factory=dict)   # por número de sesión
    justificadas: list[int] = field(default_factory=list)
    evaluaciones: dict[str, Evaluacion] = field(default_factory=dict)          # por clave (p. ej. "parcial-1")
    cerrado: bool = False

    def registrarAsistencia(self, sesion: int, finSesion: datetime, presente: bool, ahora: datetime) -> None:
        # INV-11: el Instructor registra o corrige solo dentro de 48 horas.
        if ahora - finSesion > PLAZO_INSTRUCTOR:
            raise EdicionBloqueada("Pasaron más de 48 horas; la corrección es de Control Escolar")
        self._abierto()
        self.asistencias[sesion] = AsistenciaRegistrada(presente, ahora)

    def corregirAsistencia(self, sesion: int, presente: bool, justificacion: str, ahora: datetime) -> None:
        # INV-11: después de 48 horas, Control Escolar corrige con justificación escrita del instructor.
        if not justificacion.strip():
            raise JustificacionInvalida("La corrección extemporánea requiere justificación escrita")
        self._abierto()
        self.asistencias[sesion] = AsistenciaRegistrada(presente, ahora, justificacion)

    def justificarInasistencia(self, sesion: int, presentadaEn: date, limite: date) -> bool:
        """INV-13: se presenta dentro de 5 días hábiles; solo dos por curso no cuentan contra el porcentaje.

        Devuelve True si la falta queda justificada y False si cuenta como falta (desde la tercera)."""
        if presentadaEn > limite:
            raise JustificacionInvalida("La justificación se presentó fuera de los 5 días hábiles")
        self._abierto()
        if len(self.justificadas) >= JUSTIFICACIONES_PERMITIDAS:
            return False
        self.justificadas.append(sesion)
        return True

    def capturarEvaluacion(self, clave: str, tipo: str, valor: float, instructorId: str, inscrito: bool) -> None:
        # INV-16: solo si la Inscripción está Inscrito.
        if not inscrito:
            raise InscripcionNoInscrita("La inscripción no está formalizada; no se capturan evaluaciones")
        self._abierto()
        anterior = self.evaluaciones.get(clave)
        # INV-17: un instructor sustituto no modifica evaluaciones del anterior.
        if anterior and anterior.instructorId != instructorId:
            raise EvaluacionDeOtroInstructor("La evaluación la capturó otro instructor; corrige Control Escolar")
        self.evaluaciones[clave] = Evaluacion(tipo, valor, instructorId)   # INV-14 valida el rango

    def calificacionFinal(self, ponderacion: Ponderacion) -> float:
        """INV-15: promedio por tipo, ponderado con la Ponderación del Curso."""
        total = 0.0
        for tipo in ("parcial", "proyecto", "actividad"):
            valores = [e.valor for e in self.evaluaciones.values() if e.tipo == tipo]
            if valores:
                total += sum(valores) / len(valores) * ponderacion.peso(tipo) / 100
        return round(total, 2)

    def porcentajeAsistencia(self, totalSesiones: int) -> float:
        presentes = sum(1 for a in self.asistencias.values() if a.presente)
        justificadas = sum(1 for s in self.justificadas if not self._presente(s))
        return round((presentes + justificadas) / totalSesiones * 100, 2) if totalSesiones else 0.0

    def sesionesSinRegistro(self, sesiones: range) -> list[int]:
        return [s for s in sesiones if s not in self.asistencias]

    def cerrar(self) -> None:
        """Reacción a ActaCerrada: el expediente deja de aceptar cambios (INV-22)."""
        self.cerrado = True

    def _presente(self, sesion: int) -> bool:
        a = self.asistencias.get(sesion)
        return bool(a and a.presente)

    def _abierto(self) -> None:
        if self.cerrado:
            raise ActaYaCerrada("El acta del grupo está cerrada")
