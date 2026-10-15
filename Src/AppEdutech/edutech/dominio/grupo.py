"""Aggregate Grupo: protege el cupo (INV-03) y la lista de espera (INV-04)."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .errores import SinCupo
from .eventos import (EstudianteAgregadoAListaDeEspera, LugarLiberado,
                      LugarOfrecidoAlSiguienteEnEspera, LugarReservado)
from .valores import Cupo


@dataclass
class RegistroEnListaDeEspera:
    """Entidad interna del Grupo: orden por fecha y hora (BRD, US-04)."""
    estudianteId: str
    fechaHora: datetime
    ofrecidoHasta: datetime | None = None


@dataclass
class Grupo:
    grupoId: str
    cursoId: str
    cupo: Cupo
    sesiones: list[datetime]                       # fin de cada sesión del calendario
    ocupados: list[str] = field(default_factory=list)   # inscripcionId que ocupan lugar
    listaDeEspera: list[RegistroEnListaDeEspera] = field(default_factory=list)

    @property
    def fechaInicio(self) -> date:
        return min(self.sesiones).date()

    @property
    def ultimaSesion(self) -> date:
        return max(self.sesiones).date()

    def reservarLugar(self, inscripcionId: str) -> LugarReservado:
        # INV-03: los lugares ocupados no superan la capacidad.
        if len(self.ocupados) >= self.cupo.capacidad:
            raise SinCupo("El grupo alcanzó su cupo máximo")
        self.ocupados.append(inscripcionId)
        # US-06: la fecha límite de pago es 7 días naturales desde el inicio del curso.
        return LugarReservado(self.grupoId, inscripcionId, self.fechaInicio + timedelta(days=7))

    def agregarAListaDeEspera(self, estudianteId: str, fechaHora: datetime) -> EstudianteAgregadoAListaDeEspera:
        self.listaDeEspera.append(RegistroEnListaDeEspera(estudianteId, fechaHora))
        self.listaDeEspera.sort(key=lambda r: r.fechaHora)
        return EstudianteAgregadoAListaDeEspera(self.grupoId, estudianteId, fechaHora)

    def liberarLugar(self, inscripcionId: str, ahora: datetime) -> list:
        """Libera el lugar y, si hay lista de espera, lo ofrece al primero por 24 horas (INV-04)."""
        self.ocupados.remove(inscripcionId)
        eventos = [LugarLiberado(self.grupoId, inscripcionId)]
        pendientes = [r for r in self.listaDeEspera if r.ofrecidoHasta is None]
        if pendientes:
            siguiente = pendientes[0]
            siguiente.ofrecidoHasta = ahora + timedelta(hours=24)
            eventos.append(LugarOfrecidoAlSiguienteEnEspera(self.grupoId, siguiente.estudianteId, siguiente.ofrecidoHasta))
        return eventos
