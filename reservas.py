"""
reservas.py
===========
Módulo de gestión de reservas del Sistema Integral de Software FJ.

Estados de una reserva:
    PENDIENTE → CONFIRMADA → COMPLETADA
    PENDIENTE → CANCELADA
    CONFIRMADA → CANCELADA
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from entidades import Entidad, Cliente
from servicios import Servicio
from excepciones import (
    ReservaYaConfirmadaError,
    ReservaCanceladaError,
    ReservaNoEncontradaError,
    DuracionInvalidaError,
    CalculoError,
    ServicioNoDisponibleError,
)
from logger import log


# ══════════════════════════════════════════════════════════════════════════════
# ESTADOS DE RESERVA
# ══════════════════════════════════════════════════════════════════════════════

class EstadoReserva(Enum):
    PENDIENTE   = "PENDIENTE"
    CONFIRMADA  = "CONFIRMADA"
    COMPLETADA  = "COMPLETADA"
    CANCELADA   = "CANCELADA"


# ══════════════════════════════════════════════════════════════════════════════
# CLASE RESERVA
# ══════════════════════════════════════════════════════════════════════════════

class Reserva(Entidad):
    """
    Integra un Cliente con un Servicio para gestionar la reserva completa.

    Ciclo de vida:
        1. Se crea en estado PENDIENTE.
        2. Se confirma → CONFIRMADA  (el servicio queda ocupado).
        3. Se completa → COMPLETADA  (el servicio se libera).
        4. En cualquier momento se puede cancelar → CANCELADA.

    El manejo de excepciones dentro de esta clase es exhaustivo:
        - try/except              → confirmar / cancelar
        - try/except/else         → procesar
        - try/except/finally      → calcular_costo_total
        - encadenamiento (raise … from …) → validaciones internas
    """

    DURACION_MIN = 0.5    # horas
    DURACION_MAX = 720.0  # horas (30 días)

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: float,
        notas: str = "",
        **kwargs_servicio,
    ):
        super().__init__()
        self._cliente  = self._validar_cliente(cliente)
        self._servicio = self._validar_servicio(servicio)
        self._duracion = self._validar_duracion(duracion_horas)
        self._notas    = str(notas).strip()
        self._kwargs   = kwargs_servicio      # parámetros extra al servicio
        self._estado   = EstadoReserva.PENDIENTE
        self._desglose_costo: Optional[dict] = None
        self._fecha_confirmacion: Optional[datetime] = None
        self._fecha_cancelacion : Optional[datetime] = None

        log.info(
            f"Reserva [{self._id}] creada — Cliente: {cliente.nombre_completo} "
            f"| Servicio: {servicio.nombre} | Duración: {duracion_horas}h",
            "Reserva"
        )

    # ── Propiedades ───────────────────────────────────────────────────────────

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> float:
        return self._duracion

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def notas(self) -> str:
        return self._notas

    @property
    def desglose_costo(self) -> Optional[dict]:
        return self._desglose_costo

    @property
    def fecha_confirmacion(self) -> Optional[datetime]:
        return self._fecha_confirmacion

    @property
    def fecha_cancelacion(self) -> Optional[datetime]:
        return self._fecha_cancelacion

    # ── Operaciones de ciclo de vida ──────────────────────────────────────────

    def confirmar(self, descuento_extra: float = 0.0) -> bool:
        """
        Confirma la reserva si está en estado PENDIENTE.
        Aplica el descuento del tipo de cliente + descuento_extra.

        Usa try/except para manejar fallos de disponibilidad y cálculo.
        Retorna True si la confirmación fue exitosa.
        """
        try:
            # ── Verificar estado ──────────────────────────────────────────
            if self._estado == EstadoReserva.CONFIRMADA:
                raise ReservaYaConfirmadaError(self._id)
            if self._estado == EstadoReserva.CANCELADA:
                raise ReservaCanceladaError(self._id)

            # ── Calcular costo total ──────────────────────────────────────
            descuento_total = self._cliente.descuento_por_tipo() + descuento_extra
            descuento_total = min(descuento_total, 100.0)   # no puede superar el 100 %

            self._desglose_costo = self._servicio.calcular_costo_con_extras(
                horas=self._duracion,
                descuento=descuento_total,
                **self._kwargs,
            )

            # ── Ocupar el servicio ────────────────────────────────────────
            self._servicio.ocupar()

            # ── Actualizar estado ─────────────────────────────────────────
            self._estado = EstadoReserva.CONFIRMADA
            self._fecha_confirmacion = datetime.now()
            self._cliente.agregar_reserva_id(self._id)

            log.info(
                f"Reserva [{self._id}] CONFIRMADA — "
                f"Total: $ {self._desglose_costo.get('total', 0):,.2f} COP",
                "Reserva"
            )
            return True

        except (ReservaYaConfirmadaError, ReservaCanceladaError) as exc:
            log.error(str(exc), "Reserva.confirmar")
            raise
        except ServicioNoDisponibleError as exc:
            log.error(
                f"No se pudo confirmar reserva [{self._id}]: "
                f"servicio no disponible. {exc}",
                "Reserva.confirmar"
            )
            raise
        except Exception as exc:
            log.critico(
                f"Error inesperado al confirmar reserva [{self._id}]: {exc}",
                "Reserva.confirmar",
                exc
            )
            raise CalculoError(
                f"Fallo al calcular el costo de la reserva: {exc}"
            ) from exc

    def cancelar(self, motivo: str = "") -> bool:
        """
        Cancela la reserva.  Si estaba CONFIRMADA, libera el servicio.

        Usa try/except para garantizar la liberación del servicio.
        """
        try:
            if self._estado == EstadoReserva.CANCELADA:
                raise ReservaCanceladaError(self._id)

            era_confirmada = self._estado == EstadoReserva.CONFIRMADA

            self._estado = EstadoReserva.CANCELADA
            self._fecha_cancelacion = datetime.now()

            if era_confirmada:
                self._servicio.liberar()
                self._cliente.eliminar_reserva_id(self._id)

            log.aviso(
                f"Reserva [{self._id}] CANCELADA."
                + (f" Motivo: {motivo}" if motivo else ""),
                "Reserva"
            )
            return True

        except ReservaCanceladaError as exc:
            log.error(str(exc), "Reserva.cancelar")
            raise

    def procesar(self) -> bool:
        """
        Marca la reserva como COMPLETADA una vez prestado el servicio.

        Usa try/except/else para separar el flujo normal del manejo de errores.
        """
        try:
            if self._estado != EstadoReserva.CONFIRMADA:
                raise ValueError(
                    f"Solo se pueden completar reservas CONFIRMADAS. "
                    f"Estado actual: {self._estado.value}."
                )
            self._servicio.liberar()
        except ValueError as exc:
            log.error(str(exc), "Reserva.procesar")
            raise
        except Exception as exc:
            log.critico(
                f"Error inesperado al procesar reserva [{self._id}]: {exc}",
                "Reserva.procesar",
                exc
            )
            raise
        else:
            # Este bloque solo se ejecuta si no hubo excepciones
            self._estado = EstadoReserva.COMPLETADA
            log.info(
                f"Reserva [{self._id}] COMPLETADA exitosamente.",
                "Reserva"
            )
            return True

    def calcular_costo_total(
        self,
        descuento: float = 0.0,
        tasa_iva: Optional[float] = None,
        **kwargs,
    ) -> dict:
        """
        Calcula el costo total de la reserva (puede llamarse antes de confirmar).

        Usa try/except/finally: el bloque finally garantiza el log de auditoría.
        """
        auditado = False
        try:
            descuento_total = self._cliente.descuento_por_tipo() + descuento
            descuento_total = min(descuento_total, 100.0)

            parametros = {**self._kwargs, **kwargs}
            if tasa_iva is not None:
                parametros["tasa_iva"] = tasa_iva

            desglose = self._servicio.calcular_costo_con_extras(
                horas=self._duracion,
                descuento=descuento_total,
                **parametros,
            )
            auditado = True
            return desglose

        except CalculoError as exc:
            log.error(
                f"Error de cálculo en reserva [{self._id}]: {exc}",
                "Reserva.calcular_costo_total"
            )
            raise
        except Exception as exc:
            log.critico(
                f"Fallo crítico al calcular costo reserva [{self._id}]: {exc}",
                "Reserva.calcular_costo_total",
                exc
            )
            raise CalculoError(str(exc)) from exc
        finally:
            # Siempre se registra la auditoría, haya o no excepción
            estado_log = "exitosa" if auditado else "fallida"
            log.info(
                f"Auditoría de cálculo de costo [{self._id}] — {estado_log}.",
                "Reserva.calcular_costo_total"
            )

    # ── Implementación de métodos abstractos ──────────────────────────────────

    def describir(self) -> str:
        costo_str = ""
        if self._desglose_costo:
            costo_str = f"\n  Costo total : $ {self._desglose_costo.get('total', 0):,.2f} COP"
        return (
            f"Reserva [{self._id}] — {self._estado.value}\n"
            f"  Cliente     : {self._cliente.nombre_completo}\n"
            f"  Servicio    : {self._servicio.nombre}\n"
            f"  Duración    : {self._duracion}h\n"
            f"  Notas       : {self._notas or '—'}"
            f"{costo_str}"
        )

    def validar(self) -> bool:
        return (
            self._cliente is not None and
            self._servicio is not None and
            self.DURACION_MIN <= self._duracion <= self.DURACION_MAX and
            isinstance(self._estado, EstadoReserva)
        )

    # ── Validaciones internas (con encadenamiento de excepciones) ─────────────

    @staticmethod
    def _validar_cliente(cliente) -> Cliente:
        try:
            assert isinstance(cliente, Cliente), "El objeto no es un Cliente."
            assert cliente.activo, "El cliente está inactivo."
            return cliente
        except AssertionError as exc:
            raise ValueError(
                f"Cliente inválido para la reserva: {exc}"
            ) from exc

    @staticmethod
    def _validar_servicio(servicio) -> Servicio:
        try:
            assert isinstance(servicio, Servicio), "El objeto no es un Servicio."
            return servicio
        except AssertionError as exc:
            raise ValueError(
                f"Servicio inválido para la reserva: {exc}"
            ) from exc

    @staticmethod
    def _validar_duracion(horas) -> float:
        try:
            horas = float(horas)
        except (TypeError, ValueError) as exc:
            raise DuracionInvalidaError(horas) from exc

        if not (Reserva.DURACION_MIN <= horas <= Reserva.DURACION_MAX):
            raise DuracionInvalidaError(horas, Reserva.DURACION_MIN, Reserva.DURACION_MAX)
        return horas


# ══════════════════════════════════════════════════════════════════════════════
# GESTOR DE RESERVAS
# ══════════════════════════════════════════════════════════════════════════════

class GestorReservas:
    """Repositorio en memoria de todas las reservas del sistema."""

    def __init__(self):
        self._reservas: dict[str, Reserva] = {}

    def crear(
        self,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: float,
        notas: str = "",
        **kwargs_servicio,
    ) -> Reserva:
        reserva = Reserva(cliente, servicio, duracion_horas, notas, **kwargs_servicio)
        self._reservas[reserva.id] = reserva
        return reserva

    def buscar(self, id_reserva: str) -> Reserva:
        r = self._reservas.get(id_reserva)
        if r is None:
            raise ReservaNoEncontradaError(id_reserva)
        return r

    def listar(self) -> list[Reserva]:
        return list(self._reservas.values())

    def listar_por_estado(self, estado: EstadoReserva) -> list[Reserva]:
        return [r for r in self._reservas.values() if r.estado == estado]

    def total(self) -> int:
        return len(self._reservas)
