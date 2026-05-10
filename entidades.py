"""
entidades.py
============
Define la clase abstracta base `Entidad` y la clase concreta `Cliente`
con encapsulación rigurosa y validaciones de negocio.
"""

import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from excepciones import (
    DatosClienteInvalidosError,
    ClienteYaExisteError,
    ClienteNoEncontradoError,
)
from logger import log


# ══════════════════════════════════════════════════════════════════════════════
# CLASE ABSTRACTA BASE
# ══════════════════════════════════════════════════════════════════════════════

class Entidad(ABC):
    """
    Clase abstracta raíz del sistema.
    Toda entidad gestionable (Cliente, Servicio, Reserva) hereda de aquí
    y debe implementar `describir()` y `validar()`.
    """

    def __init__(self):
        self._id: str = str(uuid.uuid4())[:8].upper()
        self._fecha_creacion: datetime = datetime.now()
        self._activo: bool = True

    # ── Propiedades comunes ───────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @property
    def activo(self) -> bool:
        return self._activo

    @activo.setter
    def activo(self, valor: bool):
        if not isinstance(valor, bool):
            raise TypeError("El campo 'activo' debe ser booleano.")
        self._activo = valor

    # ── Métodos abstractos ────────────────────────────────────────────────────

    @abstractmethod
    def describir(self) -> str:
        """Retorna una descripción legible de la entidad."""

    @abstractmethod
    def validar(self) -> bool:
        """Valida que la entidad tenga datos coherentes y completos."""

    # ── Representación ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id}>"

    def __eq__(self, otro) -> bool:
        if not isinstance(otro, Entidad):
            return NotImplemented
        return self._id == otro._id

    def __hash__(self) -> int:
        return hash(self._id)


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTE
# ══════════════════════════════════════════════════════════════════════════════

class Cliente(Entidad):
    """
    Representa un cliente de Software FJ.

    Atributos encapsulados (acceso solo mediante propiedades):
        _nombre, _apellido, _correo, _telefono, _tipo_cliente

    Tipos de cliente válidos:
        'regular', 'empresarial', 'vip'
    """

    TIPOS_VALIDOS = {"regular", "empresarial", "vip"}
    _PATRON_CORREO = re.compile(
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    _PATRON_TELEFONO = re.compile(r"^\+?[0-9\s\-()]{7,20}$")

    def __init__(
        self,
        nombre: str,
        apellido: str,
        correo: str,
        telefono: str,
        tipo_cliente: str = "regular",
    ):
        super().__init__()
        # Usamos los setters para aplicar validaciones desde el inicio
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.telefono = telefono
        self.tipo_cliente = tipo_cliente
        self._reservas_ids: list[str] = []

        log.info(
            f"Cliente creado: {self.nombre_completo} ({self._correo}) "
            f"[{self._tipo_cliente}]",
            "Cliente"
        )

    # ── Propiedades con validación ────────────────────────────────────────────

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        valor = self._limpiar_texto(valor, "nombre")
        if len(valor) < 2:
            raise DatosClienteInvalidosError(
                "nombre", valor, "Debe tener al menos 2 caracteres."
            )
        if not valor.replace(" ", "").isalpha():
            raise DatosClienteInvalidosError(
                "nombre", valor, "Solo se permiten letras y espacios."
            )
        self._nombre = valor.title()

    @property
    def apellido(self) -> str:
        return self._apellido

    @apellido.setter
    def apellido(self, valor: str):
        valor = self._limpiar_texto(valor, "apellido")
        if len(valor) < 2:
            raise DatosClienteInvalidosError(
                "apellido", valor, "Debe tener al menos 2 caracteres."
            )
        if not valor.replace(" ", "").isalpha():
            raise DatosClienteInvalidosError(
                "apellido", valor, "Solo se permiten letras y espacios."
            )
        self._apellido = valor.title()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str):
        valor = self._limpiar_texto(valor, "correo")
        if not self._PATRON_CORREO.match(valor):
            raise DatosClienteInvalidosError(
                "correo", valor, "Formato de correo electrónico inválido."
            )
        self._correo = valor.lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        valor = self._limpiar_texto(valor, "telefono")
        if not self._PATRON_TELEFONO.match(valor):
            raise DatosClienteInvalidosError(
                "telefono", valor,
                "Formato inválido. Ejemplo válido: +57 300 1234567"
            )
        self._telefono = valor

    @property
    def tipo_cliente(self) -> str:
        return self._tipo_cliente

    @tipo_cliente.setter
    def tipo_cliente(self, valor: str):
        if not isinstance(valor, str) or valor.lower() not in self.TIPOS_VALIDOS:
            raise DatosClienteInvalidosError(
                "tipo_cliente", valor,
                f"Debe ser uno de: {', '.join(sorted(self.TIPOS_VALIDOS))}."
            )
        self._tipo_cliente = valor.lower()

    @property
    def nombre_completo(self) -> str:
        return f"{self._nombre} {self._apellido}"

    @property
    def reservas_ids(self) -> list:
        return list(self._reservas_ids)  # copia defensiva

    # ── Métodos de negocio ────────────────────────────────────────────────────

    def agregar_reserva_id(self, id_reserva: str):
        """Vincula el ID de una reserva a este cliente."""
        if id_reserva not in self._reservas_ids:
            self._reservas_ids.append(id_reserva)

    def eliminar_reserva_id(self, id_reserva: str):
        """Desvincula el ID de una reserva de este cliente."""
        try:
            self._reservas_ids.remove(id_reserva)
        except ValueError:
            pass  # No estaba registrada; no es un error crítico

    def descuento_por_tipo(self) -> float:
        """Retorna el porcentaje de descuento según el tipo de cliente."""
        descuentos = {"regular": 0.0, "empresarial": 10.0, "vip": 20.0}
        return descuentos.get(self._tipo_cliente, 0.0)

    # ── Implementación de métodos abstractos ──────────────────────────────────

    def describir(self) -> str:
        return (
            f"Cliente [{self._id}]\n"
            f"  Nombre    : {self.nombre_completo}\n"
            f"  Correo    : {self._correo}\n"
            f"  Teléfono  : {self._telefono}\n"
            f"  Tipo      : {self._tipo_cliente.upper()}\n"
            f"  Reservas  : {len(self._reservas_ids)}\n"
            f"  Activo    : {'Sí' if self._activo else 'No'}"
        )

    def validar(self) -> bool:
        """
        Valida que todos los campos requeridos estén presentes y sean coherentes.
        Retorna True si la entidad es válida, False en caso contrario.
        """
        try:
            assert self._nombre and len(self._nombre) >= 2
            assert self._apellido and len(self._apellido) >= 2
            assert self._PATRON_CORREO.match(self._correo)
            assert self._PATRON_TELEFONO.match(self._telefono)
            assert self._tipo_cliente in self.TIPOS_VALIDOS
            return True
        except AssertionError:
            return False

    # ── Utilidades internas ───────────────────────────────────────────────────

    @staticmethod
    def _limpiar_texto(valor, campo: str) -> str:
        if not isinstance(valor, str):
            raise DatosClienteInvalidosError(
                campo, valor, "Debe ser una cadena de texto."
            )
        valor = valor.strip()
        if not valor:
            raise DatosClienteInvalidosError(
                campo, valor, "El campo no puede estar vacío."
            )
        return valor


# ══════════════════════════════════════════════════════════════════════════════
# REPOSITORIO DE CLIENTES
# ══════════════════════════════════════════════════════════════════════════════

class RepositorioClientes:
    """
    Gestiona la colección de clientes en memoria.
    Actúa como fuente única de verdad para todos los clientes del sistema.
    """

    def __init__(self):
        self._clientes: dict[str, Cliente] = {}   # id → Cliente
        self._correos: dict[str, str] = {}        # correo → id (índice único)

    def agregar(self, cliente: Cliente) -> Cliente:
        """
        Agrega un cliente al repositorio.
        Lanza ClienteYaExisteError si el correo o ID ya están registrados.
        """
        try:
            if cliente.id in self._clientes:
                raise ClienteYaExisteError(cliente.id)
            if cliente.correo in self._correos:
                raise ClienteYaExisteError(cliente.correo)

            self._clientes[cliente.id] = cliente
            self._correos[cliente.correo] = cliente.id
            log.info(
                f"Cliente registrado exitosamente: {cliente.nombre_completo}",
                "RepositorioClientes"
            )
            return cliente

        except ClienteYaExisteError:
            log.error(
                f"Intento de duplicado — cliente: {cliente.correo}",
                "RepositorioClientes"
            )
            raise

    def buscar_por_id(self, id_cliente: str) -> Cliente:
        """Retorna el cliente con el ID dado o lanza ClienteNoEncontradoError."""
        cliente = self._clientes.get(id_cliente)
        if cliente is None:
            raise ClienteNoEncontradoError(id_cliente)
        return cliente

    def buscar_por_correo(self, correo: str) -> Cliente:
        """Retorna el cliente con el correo dado o lanza ClienteNoEncontradoError."""
        id_c = self._correos.get(correo.lower())
        if id_c is None:
            raise ClienteNoEncontradoError(correo)
        return self._clientes[id_c]

    def listar(self) -> list[Cliente]:
        """Retorna todos los clientes registrados."""
        return list(self._clientes.values())

    def total(self) -> int:
        return len(self._clientes)

    def __len__(self) -> int:
        return self.total()
