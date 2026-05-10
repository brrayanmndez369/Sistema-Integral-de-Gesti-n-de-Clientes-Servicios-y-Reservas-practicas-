"""
servicios.py
============
Jerarquía de servicios de Software FJ.

    Servicio (abstracta)
        ├── ReservaSala
        ├── AlquilerEquipo
        └── AsesoriEspecializada

Cada subclase implementa polimorfismo en:
    - calcular_costo()          ← sobrescrito
    - describir()               ← sobrescrito
    - validar()                 ← sobrescrito
    - calcular_costo_con_extras()  ← método sobrecargado (parámetros opcionales)
"""

from abc import abstractmethod
from datetime import datetime
from typing import Optional

from entidades import Entidad
from excepciones import (
    ParametrosServicioInvalidosError,
    ServicioNoDisponibleError,
    CapacidadExcedidaError,
    DescuentoInvalidoError,
    ImpuestoInvalidoError,
    CalculoError,
)
from logger import log


# ══════════════════════════════════════════════════════════════════════════════
# CLASE ABSTRACTA: SERVICIO
# ══════════════════════════════════════════════════════════════════════════════

class Servicio(Entidad):
    """
    Clase abstracta que representa cualquier servicio ofrecido por Software FJ.

    Toda subclase debe implementar:
        - calcular_costo(horas)
        - calcular_costo_con_extras(horas, ...)
        - describir()
        - validar()
    """

    TASA_IVA_DEFAULT = 19.0   # IVA colombiano (%)

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_base_hora: float,
        capacidad_max: int = 1,
    ):
        super().__init__()
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio_base_hora = precio_base_hora
        self.capacidad_max = capacidad_max
        self._reservas_activas: int = 0
        self._disponible: bool = True

    # ── Propiedades con validación ────────────────────────────────────────────

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        if not isinstance(valor, str) or not valor.strip():
            raise ParametrosServicioInvalidosError(
                "nombre", valor, "No puede estar vacío."
            )
        self._nombre = valor.strip()

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str):
        if not isinstance(valor, str):
            raise ParametrosServicioInvalidosError(
                "descripcion", valor, "Debe ser texto."
            )
        self._descripcion = valor.strip()

    @property
    def precio_base_hora(self) -> float:
        return self._precio_base_hora

    @precio_base_hora.setter
    def precio_base_hora(self, valor: float):
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ParametrosServicioInvalidosError(
                "precio_base_hora", valor, "Debe ser un número."
            )
        if valor <= 0:
            raise ParametrosServicioInvalidosError(
                "precio_base_hora", valor, "Debe ser mayor que cero."
            )
        self._precio_base_hora = valor

    @property
    def capacidad_max(self) -> int:
        return self._capacidad_max

    @capacidad_max.setter
    def capacidad_max(self, valor: int):
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ParametrosServicioInvalidosError(
                "capacidad_max", valor, "Debe ser un entero."
            )
        if valor < 1:
            raise ParametrosServicioInvalidosError(
                "capacidad_max", valor, "Debe ser al menos 1."
            )
        self._capacidad_max = valor

    @property
    def disponible(self) -> bool:
        return self._disponible and self._reservas_activas < self._capacidad_max

    @property
    def reservas_activas(self) -> int:
        return self._reservas_activas

    # ── Métodos de control de disponibilidad ──────────────────────────────────

    def habilitar(self):
        self._disponible = True
        log.info(f"Servicio '{self._nombre}' habilitado.", "Servicio")

    def deshabilitar(self, razon: str = ""):
        self._disponible = False
        log.aviso(
            f"Servicio '{self._nombre}' deshabilitado. {razon}", "Servicio"
        )

    def ocupar(self):
        """Incrementa el contador de reservas activas."""
        if not self._disponible:
            raise ServicioNoDisponibleError(
                self._nombre, "El servicio está deshabilitado manualmente."
            )
        if self._reservas_activas >= self._capacidad_max:
            raise CapacidadExcedidaError(self._nombre, self._capacidad_max)
        self._reservas_activas += 1

    def liberar(self):
        """Decrementa el contador de reservas activas."""
        if self._reservas_activas > 0:
            self._reservas_activas -= 1

    # ── Cálculos compartidos ──────────────────────────────────────────────────

    def _validar_horas(self, horas: float, minimo: float = 0.5, maximo: float = 48.0):
        try:
            horas = float(horas)
        except (TypeError, ValueError) as exc:
            raise CalculoError(
                f"Las horas deben ser un número, se recibió: '{horas}'."
            ) from exc
        if horas < minimo or horas > maximo:
            raise CalculoError(
                f"Las horas ({horas}) deben estar entre {minimo} y {maximo}."
            )
        return horas

    def _aplicar_impuesto(self, subtotal: float, tasa_iva: float) -> float:
        if tasa_iva < 0:
            raise ImpuestoInvalidoError(tasa_iva)
        return subtotal * (1 + tasa_iva / 100)

    def _aplicar_descuento(self, subtotal: float, descuento: float) -> float:
        if not (0 <= descuento <= 100):
            raise DescuentoInvalidoError(descuento)
        return subtotal * (1 - descuento / 100)

    # ── Métodos abstractos ────────────────────────────────────────────────────

    @abstractmethod
    def calcular_costo(self, horas: float) -> float:
        """Costo base sin impuestos ni descuentos."""

    @abstractmethod
    def calcular_costo_con_extras(
        self,
        horas: float,
        descuento: float = 0.0,
        tasa_iva: Optional[float] = None,
        **kwargs,
    ) -> dict:
        """
        Método sobrecargado: calcula el costo total incluyendo descuentos,
        impuestos y otros parámetros específicos del servicio.
        Retorna un diccionario detallado con el desglose de costos.
        """

    @abstractmethod
    def describir(self) -> str:
        """Descripción completa del servicio."""

    @abstractmethod
    def validar(self) -> bool:
        """Valida la integridad de los parámetros del servicio."""

    # ── Resumen común ─────────────────────────────────────────────────────────

    def _encabezado(self) -> str:
        estado = "✔ DISPONIBLE" if self.disponible else "✘ NO DISPONIBLE"
        return (
            f"[{self.__class__.__name__} — ID: {self._id}] {self._nombre}\n"
            f"  Estado      : {estado}\n"
            f"  Precio/hora : $ {self._precio_base_hora:,.2f} COP\n"
            f"  Capacidad   : {self._reservas_activas}/{self._capacidad_max}\n"
        )


# ══════════════════════════════════════════════════════════════════════════════
# SERVICIO 1: RESERVA DE SALA
# ══════════════════════════════════════════════════════════════════════════════

class ReservaSala(Servicio):
    """
    Servicio de reserva de salas de reuniones, conferencias o coworking.

    Parámetros extra:
        aforo       : número máximo de personas permitidas
        equipada    : si la sala incluye proyector, pantalla y audio
    """

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_base_hora: float,
        aforo: int,
        equipada: bool = True,
        capacidad_max: int = 10,
    ):
        super().__init__(nombre, descripcion, precio_base_hora, capacidad_max)
        self.aforo = aforo
        self._equipada = equipada
        log.info(f"ReservaSala creada: '{self._nombre}' (aforo={aforo})", "ReservaSala")

    @property
    def aforo(self) -> int:
        return self._aforo

    @aforo.setter
    def aforo(self, valor: int):
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ParametrosServicioInvalidosError(
                "aforo", valor, "Debe ser un entero positivo."
            )
        if valor < 1:
            raise ParametrosServicioInvalidosError(
                "aforo", valor, "El aforo mínimo es 1 persona."
            )
        self._aforo = valor

    def calcular_costo(self, horas: float) -> float:
        """Costo base = precio_hora × horas."""
        horas = self._validar_horas(horas)
        costo = self._precio_base_hora * horas
        # Recargo del 15 % si la sala está equipada
        if self._equipada:
            costo *= 1.15
        return round(costo, 2)

    def calcular_costo_con_extras(
        self,
        horas: float,
        descuento: float = 0.0,
        tasa_iva: Optional[float] = None,
        personas: int = 1,
        **kwargs,
    ) -> dict:
        """
        Costo detallado.

        Parámetros sobrecargados:
            personas  : número real de asistentes (se valida contra el aforo)
            descuento : % de descuento (0–100)
            tasa_iva  : tasa de IVA; si es None usa la tasa default
        """
        if tasa_iva is None:
            tasa_iva = self.TASA_IVA_DEFAULT

        horas = self._validar_horas(horas)
        personas = int(personas)
        if personas > self._aforo:
            raise ParametrosServicioInvalidosError(
                "personas", personas,
                f"Excede el aforo máximo de la sala ({self._aforo})."
            )

        subtotal      = self.calcular_costo(horas)
        con_descuento = self._aplicar_descuento(subtotal, descuento)
        total         = self._aplicar_impuesto(con_descuento, tasa_iva)

        return {
            "servicio"       : self._nombre,
            "tipo"           : "Reserva de Sala",
            "horas"          : horas,
            "personas"       : personas,
            "subtotal"       : round(subtotal, 2),
            "descuento_pct"  : descuento,
            "descuento_valor": round(subtotal - con_descuento, 2),
            "iva_pct"        : tasa_iva,
            "iva_valor"      : round(total - con_descuento, 2),
            "total"          : round(total, 2),
            "equipada"       : self._equipada,
        }

    def describir(self) -> str:
        equip = "Sí" if self._equipada else "No"
        return (
            self._encabezado() +
            f"  Descripción : {self._descripcion}\n"
            f"  Aforo máx.  : {self._aforo} personas\n"
            f"  Equipada    : {equip} (proyector, pantalla, audio)"
        )

    def validar(self) -> bool:
        return (
            bool(self._nombre) and
            self._precio_base_hora > 0 and
            self._aforo >= 1 and
            isinstance(self._equipada, bool)
        )


# ══════════════════════════════════════════════════════════════════════════════
# SERVICIO 2: ALQUILER DE EQUIPO
# ══════════════════════════════════════════════════════════════════════════════

class AlquilerEquipo(Servicio):
    """
    Servicio de alquiler de equipos tecnológicos (laptops, cámaras, etc.).

    Parámetros extra:
        tipo_equipo   : categoría del equipo ('laptop', 'camara', 'proyector', …)
        deposito      : monto de depósito de garantía requerido
        unidades_disp : unidades disponibles en inventario
    """

    TIPOS_VALIDOS = {"laptop", "camara", "proyector", "tablet", "servidor", "otro"}

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_base_hora: float,
        tipo_equipo: str,
        deposito: float,
        unidades_disp: int = 1,
        capacidad_max: int = 5,
    ):
        super().__init__(nombre, descripcion, precio_base_hora, capacidad_max)
        self.tipo_equipo = tipo_equipo
        self.deposito = deposito
        self.unidades_disp = unidades_disp
        log.info(
            f"AlquilerEquipo creado: '{self._nombre}' "
            f"[{tipo_equipo}] unidades={unidades_disp}",
            "AlquilerEquipo"
        )

    @property
    def tipo_equipo(self) -> str:
        return self._tipo_equipo

    @tipo_equipo.setter
    def tipo_equipo(self, valor: str):
        if not isinstance(valor, str) or valor.lower() not in self.TIPOS_VALIDOS:
            raise ParametrosServicioInvalidosError(
                "tipo_equipo", valor,
                f"Debe ser uno de: {', '.join(sorted(self.TIPOS_VALIDOS))}."
            )
        self._tipo_equipo = valor.lower()

    @property
    def deposito(self) -> float:
        return self._deposito

    @deposito.setter
    def deposito(self, valor: float):
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ParametrosServicioInvalidosError(
                "deposito", valor, "Debe ser un número."
            )
        if valor < 0:
            raise ParametrosServicioInvalidosError(
                "deposito", valor, "No puede ser negativo."
            )
        self._deposito = valor

    @property
    def unidades_disp(self) -> int:
        return self._unidades_disp

    @unidades_disp.setter
    def unidades_disp(self, valor: int):
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ParametrosServicioInvalidosError(
                "unidades_disp", valor, "Debe ser un entero."
            )
        if valor < 0:
            raise ParametrosServicioInvalidosError(
                "unidades_disp", valor, "No puede ser negativo."
            )
        self._unidades_disp = valor

    def calcular_costo(self, horas: float) -> float:
        """Costo base = precio_hora × horas."""
        horas = self._validar_horas(horas, minimo=1.0, maximo=720.0)
        return round(self._precio_base_hora * horas, 2)

    def calcular_costo_con_extras(
        self,
        horas: float,
        descuento: float = 0.0,
        tasa_iva: Optional[float] = None,
        incluir_deposito: bool = True,
        unidades: int = 1,
        **kwargs,
    ) -> dict:
        """
        Costo detallado.

        Parámetros sobrecargados:
            incluir_deposito : si se suma el depósito de garantía al total
            unidades         : número de unidades a alquilar
            descuento        : % de descuento
            tasa_iva         : tasa de IVA
        """
        if tasa_iva is None:
            tasa_iva = self.TASA_IVA_DEFAULT

        horas = self._validar_horas(horas, minimo=1.0, maximo=720.0)
        unidades = int(unidades)
        if unidades < 1:
            raise ParametrosServicioInvalidosError(
                "unidades", unidades, "Debe ser al menos 1."
            )
        if unidades > self._unidades_disp:
            raise ParametrosServicioInvalidosError(
                "unidades", unidades,
                f"Solo hay {self._unidades_disp} unidades disponibles."
            )

        subtotal_unit = self.calcular_costo(horas)
        subtotal      = subtotal_unit * unidades
        con_descuento = self._aplicar_descuento(subtotal, descuento)
        total_sin_dep = self._aplicar_impuesto(con_descuento, tasa_iva)
        deposito_total = self._deposito * unidades if incluir_deposito else 0.0
        total_final    = total_sin_dep + deposito_total

        return {
            "servicio"        : self._nombre,
            "tipo"            : "Alquiler de Equipo",
            "tipo_equipo"     : self._tipo_equipo,
            "horas"           : horas,
            "unidades"        : unidades,
            "subtotal"        : round(subtotal, 2),
            "descuento_pct"   : descuento,
            "descuento_valor" : round(subtotal - con_descuento, 2),
            "iva_pct"         : tasa_iva,
            "iva_valor"       : round(total_sin_dep - con_descuento, 2),
            "deposito"        : round(deposito_total, 2),
            "total"           : round(total_final, 2),
        }

    def describir(self) -> str:
        return (
            self._encabezado() +
            f"  Descripción : {self._descripcion}\n"
            f"  Tipo equipo : {self._tipo_equipo.upper()}\n"
            f"  Unidades    : {self._unidades_disp} disponibles\n"
            f"  Depósito    : $ {self._deposito:,.2f} COP"
        )

    def validar(self) -> bool:
        return (
            bool(self._nombre) and
            self._precio_base_hora > 0 and
            self._tipo_equipo in self.TIPOS_VALIDOS and
            self._deposito >= 0 and
            self._unidades_disp >= 0
        )


# ══════════════════════════════════════════════════════════════════════════════
# SERVICIO 3: ASESORÍA ESPECIALIZADA
# ══════════════════════════════════════════════════════════════════════════════

class AsesoriaEspecializada(Servicio):
    """
    Servicio de asesoría técnica o profesional por parte de expertos de Software FJ.

    Parámetros extra:
        area          : área de especialización
        nivel_experto : 'junior', 'senior' o 'principal'
    """

    NIVELES_VALIDOS = {"junior", "senior", "principal"}
    _RECARGO_NIVEL  = {"junior": 0.0, "senior": 30.0, "principal": 70.0}

    def __init__(
        self,
        nombre: str,
        descripcion: str,
        precio_base_hora: float,
        area: str,
        nivel_experto: str = "senior",
        capacidad_max: int = 3,
    ):
        super().__init__(nombre, descripcion, precio_base_hora, capacidad_max)
        self.area = area
        self.nivel_experto = nivel_experto
        log.info(
            f"AsesoriaEspecializada creada: '{self._nombre}' "
            f"[{area} — {nivel_experto}]",
            "AsesoriaEspecializada"
        )

    @property
    def area(self) -> str:
        return self._area

    @area.setter
    def area(self, valor: str):
        if not isinstance(valor, str) or not valor.strip():
            raise ParametrosServicioInvalidosError(
                "area", valor, "No puede estar vacía."
            )
        self._area = valor.strip()

    @property
    def nivel_experto(self) -> str:
        return self._nivel_experto

    @nivel_experto.setter
    def nivel_experto(self, valor: str):
        if not isinstance(valor, str) or valor.lower() not in self.NIVELES_VALIDOS:
            raise ParametrosServicioInvalidosError(
                "nivel_experto", valor,
                f"Debe ser uno de: {', '.join(sorted(self.NIVELES_VALIDOS))}."
            )
        self._nivel_experto = valor.lower()

    def calcular_costo(self, horas: float) -> float:
        """Costo base con recargo según nivel del experto."""
        horas = self._validar_horas(horas, minimo=0.5, maximo=40.0)
        recargo = self._RECARGO_NIVEL.get(self._nivel_experto, 0.0)
        precio_efectivo = self._precio_base_hora * (1 + recargo / 100)
        return round(precio_efectivo * horas, 2)

    def calcular_costo_con_extras(
        self,
        horas: float,
        descuento: float = 0.0,
        tasa_iva: Optional[float] = None,
        urgente: bool = False,
        informe_escrito: bool = False,
        **kwargs,
    ) -> dict:
        """
        Costo detallado.

        Parámetros sobrecargados:
            urgente        : recargo del 25 % por atención urgente
            informe_escrito: costo adicional fijo de $ 150,000 COP
            descuento      : % de descuento
            tasa_iva       : tasa de IVA
        """
        if tasa_iva is None:
            tasa_iva = self.TASA_IVA_DEFAULT

        horas = self._validar_horas(horas, minimo=0.5, maximo=40.0)

        subtotal = self.calcular_costo(horas)

        recargo_urgencia = 0.0
        if urgente:
            recargo_urgencia = round(subtotal * 0.25, 2)
            subtotal += recargo_urgencia

        costo_informe = 150_000.0 if informe_escrito else 0.0
        subtotal += costo_informe

        con_descuento = self._aplicar_descuento(subtotal, descuento)
        total         = self._aplicar_impuesto(con_descuento, tasa_iva)

        return {
            "servicio"        : self._nombre,
            "tipo"            : "Asesoría Especializada",
            "area"            : self._area,
            "nivel_experto"   : self._nivel_experto,
            "horas"           : horas,
            "subtotal_base"   : round(self.calcular_costo(horas), 2),
            "recargo_urgencia": recargo_urgencia,
            "costo_informe"   : costo_informe,
            "subtotal"        : round(subtotal, 2),
            "descuento_pct"   : descuento,
            "descuento_valor" : round(subtotal - con_descuento, 2),
            "iva_pct"         : tasa_iva,
            "iva_valor"       : round(total - con_descuento, 2),
            "total"           : round(total, 2),
            "urgente"         : urgente,
            "informe_escrito" : informe_escrito,
        }

    def describir(self) -> str:
        recargo = self._RECARGO_NIVEL.get(self._nivel_experto, 0)
        return (
            self._encabezado() +
            f"  Descripción : {self._descripcion}\n"
            f"  Área        : {self._area}\n"
            f"  Nivel       : {self._nivel_experto.upper()} "
            f"(recargo +{recargo}%)"
        )

    def validar(self) -> bool:
        return (
            bool(self._nombre) and
            self._precio_base_hora > 0 and
            bool(self._area) and
            self._nivel_experto in self.NIVELES_VALIDOS
        )


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE SERVICIOS
# ══════════════════════════════════════════════════════════════════════════════

class CatalogoServicios:
    """Repositorio en memoria de todos los servicios disponibles."""

    def __init__(self):
        self._servicios: dict[str, Servicio] = {}

    def agregar(self, servicio: Servicio) -> Servicio:
        from excepciones import ServicioNoEncontradoError
        if not servicio.validar():
            raise ParametrosServicioInvalidosError(
                "servicio", servicio, "El servicio no pasó la validación interna."
            )
        self._servicios[servicio.id] = servicio
        log.info(
            f"Servicio registrado en catálogo: '{servicio.nombre}' [{servicio.id}]",
            "CatalogoServicios"
        )
        return servicio

    def buscar(self, id_servicio: str) -> Servicio:
        from excepciones import ServicioNoEncontradoError
        srv = self._servicios.get(id_servicio)
        if srv is None:
            raise ServicioNoEncontradoError(id_servicio)
        return srv

    def listar(self) -> list[Servicio]:
        return list(self._servicios.values())

    def listar_disponibles(self) -> list[Servicio]:
        return [s for s in self._servicios.values() if s.disponible]

    def total(self) -> int:
        return len(self._servicios)
