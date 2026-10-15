"""Puertos de la aplicación: interfaces que implementa la infraestructura."""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime


class UnitOfWork(ABC):
    """Delimita la transacción de un caso de uso (ADR-02)."""
    @abstractmethod
    def iniciar(self) -> None: ...
    @abstractmethod
    def confirmar(self) -> None: ...
    @abstractmethod
    def cancelar(self) -> None: ...


@contextmanager
def transaccion(uow: UnitOfWork):
    """Inicia, confirma o cancela: si algo falla no se guarda nada."""
    uow.iniciar()
    try:
        yield
    except Exception:
        uow.cancelar()
        raise
    uow.confirmar()


class NotificacionGateway(ABC):
    @abstractmethod
    def notificarLugarDisponible(self, estudianteId: str, vence: datetime) -> None: ...


class ControlDeAcceso(ABC):
    """La autenticación no es regla del dominio: la Service Layer comprueba el rol (D-06)."""
    @abstractmethod
    def tieneRol(self, usuarioId: str, rol: str) -> bool: ...


class AccesoDenegado(Exception):
    """El usuario no tiene el rol que pide la operación."""


def exigirRol(acceso: ControlDeAcceso, usuarioId: str, *roles: str) -> None:
    if not any(acceso.tieneRol(usuarioId, r) for r in roles):
        raise AccesoDenegado("Se requiere el rol " + " o ".join(roles))


@dataclass(frozen=True)
class VerificacionPublicaDto:
    """Solo lo que CU-05 permite mostrar: sin contacto ni calificaciones (US-19)."""
    titular: str
    curso: str
    fechaConclusion: date
    vigencia: str


@dataclass(frozen=True)
class EstadoDePagoDto:
    """Lo que el estudiante consulta de su pago (US-06)."""
    estado: str
    saldoPendiente: float
    fechaLimitePago: date


class VerificacionPublicaReader(ABC):
    """Modelo de lectura de la verificación pública (ADR-03)."""
    @abstractmethod
    def consultar(self, folio: str) -> VerificacionPublicaDto | None: ...


class EstadoDePagoReader(ABC):
    @abstractmethod
    def consultar(self, inscripcionId: str) -> EstadoDePagoDto | None: ...
