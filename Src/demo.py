"""Recorrido de demostración: un curso completo de CU-01 a CU-05.

Uso, desde la raíz del repositorio:  python Src/demo.py"""
from datetime import date, datetime, timedelta

from edutech.aplicacion.inscripcion_service import SolicitarInscripcion
from edutech.dominio.curso import Curso
from edutech.dominio.grupo import Grupo
from edutech.dominio.valores import Cupo, Modalidad
from edutech.sistema import Sistema

inicio = datetime(2026, 11, 2, 20, 0)
sesiones = [inicio + timedelta(days=d) for d in (0, 1, 2, 3, 4, 7, 8, 9, 10, 11)]
s = Sistema({"inst-1": {"Instructor"}, "coord-1": {"CoordinacionAcademica"}})
s.cursos.guardar(Curso("C-1", "Análisis de datos", Modalidad.PRESENCIAL, 4000))
s.grupos.guardar(Grupo("G-1", "C-1", Cupo(Modalidad.PRESENCIAL.cupoMaximo), sesiones))

print("CU-01  Solicitar inscripción")
r = s.inscripcion.solicitarInscripcion(SolicitarInscripcion(
    "E-1", "G-1", {"nombre": "Ana López", "correo": "ana@example.com", "telefono": "8100000000"},
    datetime(2026, 10, 20, 10, 0)))
print("       ", r)
print("        Pago del 50%:", s.contable.pagoNotificado(r.inscripcionId, 2000, date(2026, 10, 25)))
print("        Estado de pago:", s.estadoDePago.consultarEstadoDePago(r.inscripcionId))

print("CU-02  Asistencia de las 10 sesiones")
for n, fin in enumerate(sesiones, start=1):
    pct = s.asistencia.registrarAsistencia(r.inscripcionId, n, True, "inst-1", fin + timedelta(hours=1))
print("        Porcentaje de asistencia:", pct)

print("CU-03  Evaluaciones")
for clave, tipo, valor in (("parcial-1", "parcial", 80), ("proyecto", "proyecto", 90), ("actividades", "actividad", 70)):
    final = s.calificacion.capturarEvaluacion(r.inscripcionId, clave, tipo, valor, "inst-1")
print("        Calificación final:", final)

print("CU-04  Cierre de acta")
acta = s.acta.cerrarActa("G-1", date(2026, 11, 20))
for linea in acta.lineas:
    print("       ", linea)

print("US-15  Emisión del certificado")
cert = s.certificado.emitirCertificado("G-1", r.inscripcionId, "coord-1", date(2026, 11, 23))
print("        Folio:", cert.folio, "| QR:", cert.codigoQr)

print("CU-05  Verificación pública")
print("       ", s.verificacion.consultarCertificado(cert.codigoQr))
