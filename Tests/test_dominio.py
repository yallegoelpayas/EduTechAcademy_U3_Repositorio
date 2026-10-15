"""Pruebas de invariantes del dominio, sin base de datos."""
import unittest
from datetime import date, datetime, timedelta

import apoyo  # noqa: F401  (agrega Src al path)
from edutech.dominio.acta import Acta
from edutech.dominio.certificado import Certificado
from edutech.dominio.errores import (ActaConSesionesSinAsistencia, ActaYaCerrada, DatosIncompletos,
                                     EdicionBloqueada, EvaluacionDeOtroInstructor, EvaluacionFueraDeRango,
                                     InscripcionNoInscrita, NoCumpleCriterios, PonderacionInvalida, SinCupo,
                                     SobrecupoNoPermitido)
from edutech.dominio.expediente import ExpedienteAcademico
from edutech.dominio.grupo import Grupo
from edutech.dominio.inscripcion import EstadoInscripcion, Inscripcion
from edutech.dominio.servicios import CalendarioDeDiasHabiles
from edutech.dominio.valores import (AsistenciaRegistrada, CriterioDeCertificacion, Cupo, LineaDeActa, Modalidad,
                                     PagoAcreditado, Ponderacion)

AHORA = datetime(2026, 11, 2, 20, 0)


class PonderacionYCriterio(unittest.TestCase):
    def test_INV01_la_ponderacion_debe_sumar_100(self):
        self.assertEqual(Ponderacion().peso("parcial"), 40)
        with self.assertRaises(PonderacionInvalida):
            Ponderacion(50, 40, 20)

    def test_INV15_calificacion_final_ponderada_80_90_70_da_82(self):          # US-12
        e = ExpedienteAcademico("1", "C-1", "G-1")
        e.capturarEvaluacion("parcial-1", "parcial", 80, "inst-1", inscrito=True)
        e.capturarEvaluacion("proyecto", "proyecto", 90, "inst-1", inscrito=True)
        e.capturarEvaluacion("actividades", "actividad", 70, "inst-1", inscrito=True)
        self.assertEqual(e.calificacionFinal(Ponderacion()), 82)

    def test_INV21_criterio_regular_y_oficial(self):                          # US-14
        self.assertEqual(CriterioDeCertificacion.regular().evaluar(75, 85), (True, None))
        self.assertEqual(CriterioDeCertificacion.oficial().evaluar(75, 95), (False, "calificación"))
        self.assertEqual(CriterioDeCertificacion.regular().evaluar(90, 70), (False, "asistencia"))


class CupoYListaDeEspera(unittest.TestCase):
    def test_INV03_cupo_por_modalidad_y_sobrecupo_maximo_10(self):
        self.assertEqual(Modalidad.PRESENCIAL.cupoMaximo, 25)
        self.assertEqual(Modalidad.EN_LINEA.cupoMaximo, 40)
        self.assertEqual(Cupo(25, 2).capacidad, 27)
        with self.assertRaises(SobrecupoNoPermitido):
            Cupo(25, 3)

    def test_INV03_grupo_lleno_rechaza_la_reserva(self):
        g = Grupo("G", "C", Cupo(1), [AHORA])
        g.reservarLugar("1")
        with self.assertRaises(SinCupo):
            g.reservarLugar("2")

    def test_INV04_al_liberar_se_ofrece_al_primero_por_24_horas(self):
        g = Grupo("G", "C", Cupo(1), [AHORA])
        g.reservarLugar("1")
        g.agregarAListaDeEspera("tarde", AHORA + timedelta(hours=2))
        g.agregarAListaDeEspera("temprano", AHORA + timedelta(hours=1))
        eventos = g.liberarLugar("1", AHORA)
        self.assertEqual(eventos[1].estudianteId, "temprano")
        self.assertEqual(eventos[1].vence, AHORA + timedelta(hours=24))


class InscripcionYPago(unittest.TestCase):
    def nueva(self):
        return Inscripcion.preinscribir("1", "E", "G", {"nombre": "Ana", "correo": "a@x", "telefono": "1"},
                                        4000, date(2026, 11, 9))

    def test_REG01_datos_incompletos_no_se_registran(self):                   # US-04
        with self.assertRaises(DatosIncompletos):
            Inscripcion.preinscribir("1", "E", "G", {"nombre": "Ana"}, 4000, date(2026, 11, 9))

    def test_INV06_INV08_primera_parcialidad_formaliza_y_genera_folio_una_vez(self):   # US-05
        i = self.nueva()
        evento = i.registrarPago(PagoAcreditado(2000, date(2026, 11, 3)))
        self.assertEqual(i.estado, EstadoInscripcion.INSCRITO)
        self.assertEqual(evento.folio, "INS-1")
        self.assertIsNone(i.registrarPago(PagoAcreditado(2000, date(2026, 11, 5))))
        self.assertEqual((i.folio, i.saldoPendiente), ("INS-1", 0))

    def test_INV07_pago_menor_al_50_es_abono(self):                           # US-05
        i = self.nueva()
        i.registrarPago(PagoAcreditado(1000, date(2026, 11, 3)))
        self.assertEqual((i.estado, i.saldoPendiente), (EstadoInscripcion.PREINSCRITO, 3000))

    def test_INV09_plazo_vencido_libera_y_la_prorroga_lo_extiende(self):      # US-06
        i = self.nueva()
        self.assertIsNone(i.vencerPlazo(date(2026, 11, 9)))
        i.autorizarProrroga(date(2026, 11, 12))
        self.assertIsNone(i.vencerPlazo(date(2026, 11, 10)))
        self.assertIsNotNone(i.vencerPlazo(date(2026, 11, 13)))
        self.assertEqual(i.estado, EstadoInscripcion.LIBERADA)


class AsistenciaYEvaluaciones(unittest.TestCase):
    def test_INV11_instructor_bloqueado_despues_de_48_horas(self):            # US-11
        e = ExpedienteAcademico("1", "C", "G")
        e.registrarAsistencia(1, AHORA, True, AHORA + timedelta(hours=47))
        with self.assertRaises(EdicionBloqueada):
            e.registrarAsistencia(1, AHORA, False, AHORA + timedelta(hours=49))
        e.corregirAsistencia(1, False, "Error de captura reportado por el instructor", AHORA + timedelta(days=3))
        self.assertFalse(e.asistencias[1].presente)

    def test_INV12_asistencia_en_linea(self):
        self.assertTrue(AsistenciaRegistrada.acreditaEnLinea(60, None))
        self.assertTrue(AsistenciaRegistrada.acreditaEnLinea(10, 72))
        self.assertFalse(AsistenciaRegistrada.acreditaEnLinea(59, 73))

    def test_INV13_solo_dos_justificaciones_cuentan(self):
        e = ExpedienteAcademico("1", "C", "G")
        resultados = [e.justificarInasistencia(s, date(2026, 11, 3), date(2026, 11, 9)) for s in (1, 2, 3)]
        self.assertEqual(resultados, [True, True, False])

    def test_INV14_INV16_INV17_reglas_de_captura(self):                       # US-12, US-17
        e = ExpedienteAcademico("1", "C", "G")
        with self.assertRaises(InscripcionNoInscrita):
            e.capturarEvaluacion("parcial-1", "parcial", 80, "inst-1", inscrito=False)
        with self.assertRaises(EvaluacionFueraDeRango):
            e.capturarEvaluacion("parcial-1", "parcial", 101, "inst-1", inscrito=True)
        e.capturarEvaluacion("parcial-1", "parcial", 80, "inst-1", inscrito=True)
        with self.assertRaises(EvaluacionDeOtroInstructor):
            e.capturarEvaluacion("parcial-1", "parcial", 95, "inst-2", inscrito=True)


class ActaYCertificado(unittest.TestCase):
    def test_INV19_no_cierra_con_sesiones_sin_asistencia(self):              # US-13
        with self.assertRaises(ActaConSesionesSinAsistencia):
            Acta("G", "Curso").cerrar([], [3], date(2026, 12, 1), date(2026, 11, 20), date(2026, 11, 13))

    def test_INV22_INV23_acta_cerrada_y_certificado(self):                   # US-15
        acta = Acta("G", "Curso")
        linea = LineaDeActa("1", "Ana", 85, 90, True, None)
        acta.cerrar([linea, LineaDeActa("2", "Luis", 60, 90, False, "calificación")], [], date(2026, 11, 20),
                    date(2026, 11, 20), date(2026, 11, 13))
        with self.assertRaises(ActaYaCerrada):
            acta.cerrar([], [], date(2026, 11, 21), date(2026, 11, 20), date(2026, 11, 13))
        cert, _ = Certificado.emitir(acta, "1", "coord-1", date(2026, 11, 23), date(2026, 12, 4))
        self.assertEqual((cert.folio, cert.dentroDePlazo), ("CERT-1", True))
        with self.assertRaises(NoCumpleCriterios):
            Certificado.emitir(acta, "2", "coord-1", date(2026, 11, 23), date(2026, 12, 4))

    def test_calendario_de_dias_habiles_salta_fines_de_semana(self):
        self.assertEqual(CalendarioDeDiasHabiles().sumarDiasHabiles(date(2026, 11, 13), 5), date(2026, 11, 20))


if __name__ == "__main__":
    unittest.main()
