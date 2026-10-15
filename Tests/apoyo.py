"""Datos de prueba comunes."""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Src"))

from edutech.dominio.curso import Curso                       # noqa: E402
from edutech.dominio.grupo import Grupo                       # noqa: E402
from edutech.dominio.valores import Cupo, Modalidad           # noqa: E402
from edutech.sistema import Sistema                           # noqa: E402

INICIO = datetime(2026, 11, 2, 20, 0)          # lunes; cada sesión termina a las 20:00
SESIONES = [INICIO + timedelta(days=d) for d in (0, 1, 2, 3, 4, 7, 8, 9, 10, 11)]   # 10 sesiones hábiles
ROLES = {"inst-1": {"Instructor"}, "inst-2": {"Instructor"}, "ce-1": {"ControlEscolar"},
         "coord-1": {"CoordinacionAcademica"}}


def datos(nombre="Ana López"):
    return {"nombre": nombre, "correo": "ana@example.com", "telefono": "8100000000"}


def sistemaConGrupo(maximo=25, sobrecupo=0, modalidad=Modalidad.PRESENCIAL):
    s = Sistema(ROLES)
    s.cursos.guardar(Curso("C-1", "Análisis de datos", modalidad, 4000))
    s.grupos.guardar(Grupo("G-1", "C-1", Cupo(maximo, sobrecupo), list(SESIONES)))
    return s
