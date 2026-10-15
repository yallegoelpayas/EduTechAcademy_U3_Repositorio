"""Errores del dominio con nombres del negocio (revisión obligatoria de la Etapa 4)."""


class ErrorDeDominio(Exception):
    """Una regla del negocio impide la operación."""


class DatosIncompletos(ErrorDeDominio):
    """REG-01: falta un dato obligatorio de la solicitud (US-04)."""


class SinCupo(ErrorDeDominio):
    """INV-03: el grupo alcanzó su cupo máximo."""


class SobrecupoNoPermitido(ErrorDeDominio):
    """INV-03: el sobrecupo supera el 10% del cupo máximo."""


class PonderacionInvalida(ErrorDeDominio):
    """INV-01: la ponderación no suma 100."""


class EdicionBloqueada(ErrorDeDominio):
    """INV-11: pasaron más de 48 horas desde la sesión."""


class JustificacionInvalida(ErrorDeDominio):
    """INV-11 e INV-13: falta la justificación escrita o se presentó fuera de plazo."""


class EvaluacionFueraDeRango(ErrorDeDominio):
    """INV-14: la evaluación no está entre 0 y 100."""


class InscripcionNoInscrita(ErrorDeDominio):
    """INV-16: solo se capturan evaluaciones de inscripciones en estado Inscrito."""


class EvaluacionDeOtroInstructor(ErrorDeDominio):
    """INV-17: un instructor no modifica evaluaciones capturadas por otro."""


class ActaAunNoPuedeCerrarse(ErrorDeDominio):
    """INV-18: todavía no se cumplen 5 días hábiles desde la última sesión."""


class ActaConSesionesSinAsistencia(ErrorDeDominio):
    """INV-19: hay sesiones sin asistencia capturada."""


class ActaYaCerrada(ErrorDeDominio):
    """INV-22: un acta cerrada no se modifica."""


class NoCumpleCriterios(ErrorDeDominio):
    """INV-23: el certificado solo se emite si el acta está cerrada y el estudiante cumple."""


class CertificadoNoAutorizado(ErrorDeDominio):
    """INV-24: la emisión requiere la autorización de Coordinación Académica."""


class NoEncontrado(ErrorDeDominio):
    """El objeto solicitado no existe."""
