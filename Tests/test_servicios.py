"""Pruebas de los casos de uso a través de la Service Layer, con SQLite en memoria."""
import unittest
from dataclasses import asdict
from datetime import date, datetime, timedelta

from apoyo import SESIONES, datos, sistemaConGrupo
from edutech.aplicacion.inscripcion_service import EnListaDeEspera, SolicitarInscripcion, SolicitudRegistrada
from edutech.aplicacion.puertos import AccesoDenegado
from edutech.dominio.errores import CertificadoNoAutorizado, DatosIncompletos, EdicionBloqueada, NoEncontrado
from edutech.dominio.inscripcion import EstadoInscripcion

ANTES = datetime(2026, 10, 20, 10, 0)


def solicitar(s, estudiante="E-1", nombre="Ana López", ahora=ANTES):
    return s.inscripcion.solicitarInscripcion(SolicitarInscripcion(estudiante, "G-1", datos(nombre), ahora))


class CU01Inscripcion(unittest.TestCase):
    def test_SEQ01_solicitud_con_lugar_queda_preinscrita(self):               # US-04
        s = sistemaConGrupo()
        r = solicitar(s)
        self.assertIsInstance(r, SolicitudRegistrada)
        self.assertEqual((r.estado, r.monto, r.fechaLimitePago), ("Preinscrito", 4000, date(2026, 11, 9)))
        self.assertEqual(s.grupos.obtener("G-1").ocupados, [r.inscripcionId])
        self.assertEqual(s.expedientes.obtener(r.inscripcionId).grupoId, "G-1")

    def test_grupo_lleno_manda_a_lista_de_espera(self):                      # US-03, US-04
        s = sistemaConGrupo(maximo=1)
        solicitar(s)
        r = solicitar(s, "E-2", "Luis")
        self.assertIsInstance(r, EnListaDeEspera)
        self.assertEqual(s.grupos.obtener("G-1").listaDeEspera[0].estudianteId, "E-2")

    def test_datos_incompletos_no_guardan_nada(self):                        # US-04, ADR-02
        s = sistemaConGrupo()
        with self.assertRaises(DatosIncompletos):
            s.inscripcion.solicitarInscripcion(SolicitarInscripcion("E-1", "G-1", {"nombre": "Ana"}, ANTES))
        self.assertEqual(s.grupos.obtener("G-1").ocupados, [])   # el lugar reservado se revirtió

    def test_pago_del_50_por_ciento_formaliza_y_la_consulta_lo_muestra(self):  # US-05, US-06
        s = sistemaConGrupo()
        r = solicitar(s)
        self.assertEqual(s.estadoDePago.consultarEstadoDePago(r.inscripcionId).saldoPendiente, 4000)
        evento = s.contable.pagoNotificado(r.inscripcionId, 2000, date(2026, 10, 25))
        self.assertEqual(evento.folio, f"INS-{r.inscripcionId}")
        dto = s.estadoDePago.consultarEstadoDePago(r.inscripcionId)
        self.assertEqual((dto.estado, dto.saldoPendiente), ("Inscrito", 2000))

    def test_SEQ02_plazo_vencido_libera_y_ofrece_al_primero_en_espera(self):  # US-06
        s = sistemaConGrupo(maximo=1)
        r = solicitar(s)
        solicitar(s, "E-2", "Luis")
        hoy = datetime(2026, 11, 10, 9, 0)
        eventos = s.inscripcion.liberarPorPlazoVencido(r.inscripcionId, hoy)
        self.assertEqual([type(e).__name__ for e in eventos],
                         ["PlazoDePagoVencido", "LugarLiberado", "LugarOfrecidoAlSiguienteEnEspera"])
        self.assertEqual(s.inscripciones.obtener(r.inscripcionId).estado, EstadoInscripcion.LIBERADA)
        self.assertEqual(s.grupos.obtener("G-1").ocupados, [])
        self.assertEqual(s.notificaciones.enviadas, [("E-2", hoy + timedelta(hours=24))])

    def test_SEQ02_plazo_no_vencido_no_cambia_nada(self):
        s = sistemaConGrupo()
        r = solicitar(s)
        self.assertEqual(s.inscripcion.liberarPorPlazoVencido(r.inscripcionId, datetime(2026, 11, 9, 9)), [])

    def test_SEQ02_si_falla_guardar_el_grupo_no_se_libera_la_inscripcion(self):   # ADR-02
        s = sistemaConGrupo()
        r = solicitar(s)
        original = s.grupos.guardar
        s.grupos.guardar = lambda g: (_ for _ in ()).throw(RuntimeError("falla de base de datos"))
        with self.assertRaises(RuntimeError):
            s.inscripcion.liberarPorPlazoVencido(r.inscripcionId, datetime(2026, 11, 10, 9))
        s.grupos.guardar = original
        self.assertEqual(s.inscripciones.obtener(r.inscripcionId).estado, EstadoInscripcion.PREINSCRITO)
        self.assertEqual(s.notificaciones.enviadas, [])


class CursoCompleto(unittest.TestCase):
    """Recorre CU-01 a CU-05 con un estudiante que cumple y uno que no."""

    def setUp(self):
        s = self.s = sistemaConGrupo()
        self.ana = solicitar(s, "E-1", "Ana López").inscripcionId
        self.luis = solicitar(s, "E-2", "Luis Pérez").inscripcionId
        for i in (self.ana, self.luis):
            s.contable.pagoNotificado(i, 4000, date(2026, 10, 25))

    def capturarTodo(self, faltasLuis=3):
        s = self.s
        for n, fin in enumerate(SESIONES, start=1):
            s.asistencia.registrarAsistencia(self.ana, n, True, "inst-1", fin + timedelta(hours=1))
            s.asistencia.registrarAsistencia(self.luis, n, n > faltasLuis, "inst-1", fin + timedelta(hours=1))
        for i, (p, pr, a) in ((self.ana, (85, 90, 80)), (self.luis, (90, 90, 90))):
            s.calificacion.capturarEvaluacion(i, "parcial-1", "parcial", p, "inst-1")
            s.calificacion.capturarEvaluacion(i, "proyecto", "proyecto", pr, "inst-1")
            s.calificacion.capturarEvaluacion(i, "actividades", "actividad", a, "inst-1")

    def test_CU02_rol_y_plazo_de_48_horas(self):
        s = self.s
        with self.assertRaises(AccesoDenegado):
            s.asistencia.registrarAsistencia(self.ana, 1, True, "ce-1", SESIONES[0])
        with self.assertRaises(EdicionBloqueada):
            s.asistencia.registrarAsistencia(self.ana, 1, True, "inst-1", SESIONES[0] + timedelta(hours=50))

    def test_CU02_lms_acredita_asistencia_en_linea(self):
        pct = self.s.lms.conexionReportada(self.ana, 1, 65, None, SESIONES[0] + timedelta(hours=1))
        self.assertEqual(pct, 10.0)    # 1 de 10 sesiones

    def test_CU04_CU05_cierre_emision_y_verificacion_publica(self):
        s = self.s
        self.capturarTodo()
        acta = s.acta.cerrarActa("G-1", date(2026, 11, 20))     # última sesión 13/11 + 5 días hábiles
        resultados = {l.estudiante: (l.cumple, l.motivo) for l in acta.lineas}
        self.assertEqual(resultados, {"Ana López": (True, None), "Luis Pérez": (False, "asistencia")})
        with self.assertRaises(CertificadoNoAutorizado):
            s.certificado.emitirCertificado("G-1", self.ana, "inst-1", date(2026, 11, 23))
        cert = s.certificado.emitirCertificado("G-1", self.ana, "coord-1", date(2026, 11, 23))
        dto = s.verificacion.consultarCertificado(cert.codigoQr)
        self.assertEqual(set(asdict(dto)), {"titular", "curso", "fechaConclusion", "vigencia"})   # US-19
        self.assertEqual((dto.titular, dto.curso), ("Ana López", "Análisis de datos"))
        with self.assertRaises(NoEncontrado):
            s.verificacion.consultarCertificado("CERT-99999")

    def test_CU04_no_cierra_antes_de_5_dias_habiles_ni_con_sesiones_sin_asistencia(self):
        from edutech.dominio.errores import ActaAunNoPuedeCerrarse, ActaConSesionesSinAsistencia
        s = self.s
        with self.assertRaises(ActaConSesionesSinAsistencia):
            s.acta.cerrarActa("G-1", date(2026, 11, 20))
        self.capturarTodo()
        with self.assertRaises(ActaAunNoPuedeCerrarse):
            s.acta.cerrarActa("G-1", date(2026, 11, 19))


if __name__ == "__main__":
    unittest.main()
