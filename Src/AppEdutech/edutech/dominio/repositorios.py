"""Interfaces de Repository: hablan en términos del dominio, sin SQL (Etapa 5)."""
from abc import ABC, abstractmethod

from .acta import Acta
from .certificado import Certificado
from .curso import Curso
from .expediente import ExpedienteAcademico
from .grupo import Grupo
from .inscripcion import Inscripcion


class CursoRepository(ABC):
    @abstractmethod
    def obtener(self, cursoId: str) -> Curso: ...
    @abstractmethod
    def guardar(self, curso: Curso) -> None: ...


class GrupoRepository(ABC):
    @abstractmethod
    def obtener(self, grupoId: str) -> Grupo: ...
    @abstractmethod
    def guardar(self, grupo: Grupo) -> None: ...


class InscripcionRepository(ABC):
    @abstractmethod
    def obtener(self, inscripcionId: str) -> Inscripcion: ...
    @abstractmethod
    def agregar(self, inscripcion: Inscripcion) -> None: ...
    @abstractmethod
    def guardar(self, inscripcion: Inscripcion) -> None: ...
    @abstractmethod
    def delGrupo(self, grupoId: str) -> list[Inscripcion]: ...
    @abstractmethod
    def siguienteId(self) -> str: ...


class ExpedienteRepository(ABC):
    @abstractmethod
    def obtener(self, inscripcionId: str) -> ExpedienteAcademico: ...
    @abstractmethod
    def guardar(self, expediente: ExpedienteAcademico) -> None: ...


class ActaRepository(ABC):
    @abstractmethod
    def obtener(self, grupoId: str) -> Acta: ...
    @abstractmethod
    def guardar(self, acta: Acta) -> None: ...


class CertificadoRepository(ABC):
    @abstractmethod
    def agregar(self, certificado: Certificado) -> None: ...
