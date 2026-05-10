"""
excepciones.py
==============
Módulo de excepciones personalizadas para el Sistema Integral de Gestión
de Software FJ.
"""


class SistemaFJError(Exception):
    """Excepción base del sistema. Todas las excepciones personalizadas
    heredan de esta clase."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL"):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo

    def __str__(self):
        return f"[{self.codigo}] {self.mensaje}"


# ── Excepciones de Cliente ────────────────────────────────────────────────────

class ClienteError(SistemaFJError):
    """Error genérico relacionado con clientes."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_CLIENTE")


class ClienteYaExisteError(ClienteError):
    """Se intenta registrar un cliente con un ID o correo ya existente."""
    def __init__(self, identificador: str):
        super().__init__(
            f"El cliente con identificador '{identificador}' ya existe en el sistema."
        )
        self.codigo = "ERR_CLIENTE_DUPLICADO"


class ClienteNoEncontradoError(ClienteError):
    """El cliente solicitado no existe en el sistema."""
    def __init__(self, identificador: str):
        super().__init__(
            f"No se encontró ningún cliente con identificador '{identificador}'."
        )
        self.codigo = "ERR_CLIENTE_NO_ENCONTRADO"


class DatosClienteInvalidosError(ClienteError):
    """Los datos proporcionados para crear/editar un cliente son inválidos."""
    def __init__(self, campo: str, valor, razon: str = ""):
        detalle = f" Razón: {razon}" if razon else ""
        super().__init__(
            f"Valor inválido para el campo '{campo}': '{valor}'.{detalle}"
        )
        self.codigo = "ERR_CLIENTE_DATOS_INVALIDOS"
        self.campo = campo


# ── Excepciones de Servicio ───────────────────────────────────────────────────

class ServicioError(SistemaFJError):
    """Error genérico relacionado con servicios."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_SERVICIO")


class ServicioNoDisponibleError(ServicioError):
    """El servicio solicitado no está disponible en este momento."""
    def __init__(self, nombre_servicio: str, razon: str = ""):
        detalle = f" Razón: {razon}" if razon else ""
        super().__init__(
            f"El servicio '{nombre_servicio}' no está disponible.{detalle}"
        )
        self.codigo = "ERR_SERVICIO_NO_DISPONIBLE"


class ServicioNoEncontradoError(ServicioError):
    """El servicio con el ID dado no existe en el catálogo."""
    def __init__(self, id_servicio: str):
        super().__init__(
            f"No se encontró el servicio con ID '{id_servicio}'."
        )
        self.codigo = "ERR_SERVICIO_NO_ENCONTRADO"


class ParametrosServicioInvalidosError(ServicioError):
    """Los parámetros de configuración del servicio son inválidos."""
    def __init__(self, campo: str, valor, razon: str = ""):
        detalle = f" Razón: {razon}" if razon else ""
        super().__init__(
            f"Parámetro de servicio inválido — '{campo}': '{valor}'.{detalle}"
        )
        self.codigo = "ERR_SERVICIO_PARAMETROS_INVALIDOS"
        self.campo = campo


class CapacidadExcedidaError(ServicioError):
    """La capacidad máxima del servicio ha sido alcanzada."""
    def __init__(self, nombre_servicio: str, capacidad_max: int):
        super().__init__(
            f"El servicio '{nombre_servicio}' ha alcanzado su capacidad "
            f"máxima de {capacidad_max} reservas simultáneas."
        )
        self.codigo = "ERR_SERVICIO_CAPACIDAD_EXCEDIDA"


# ── Excepciones de Reserva ────────────────────────────────────────────────────

class ReservaError(SistemaFJError):
    """Error genérico relacionado con reservas."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_RESERVA")


class ReservaNoEncontradaError(ReservaError):
    """La reserva con el ID dado no existe."""
    def __init__(self, id_reserva: str):
        super().__init__(
            f"No se encontró la reserva con ID '{id_reserva}'."
        )
        self.codigo = "ERR_RESERVA_NO_ENCONTRADA"


class ReservaYaConfirmadaError(ReservaError):
    """La reserva ya está confirmada y no puede modificarse."""
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya fue confirmada anteriormente."
        )
        self.codigo = "ERR_RESERVA_YA_CONFIRMADA"


class ReservaCanceladaError(ReservaError):
    """Se intenta operar sobre una reserva ya cancelada."""
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' fue cancelada y no puede modificarse."
        )
        self.codigo = "ERR_RESERVA_CANCELADA"


class DuracionInvalidaError(ReservaError):
    """La duración especificada para la reserva es inválida."""
    def __init__(self, duracion, minimo: float = 0.5, maximo: float = 48.0):
        super().__init__(
            f"Duración '{duracion}' horas inválida. Debe estar entre "
            f"{minimo} y {maximo} horas."
        )
        self.codigo = "ERR_RESERVA_DURACION_INVALIDA"


# ── Excepciones de Cálculo ────────────────────────────────────────────────────

class CalculoError(SistemaFJError):
    """Error en operaciones de cálculo de costos u otros valores numéricos."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_CALCULO")


class DescuentoInvalidoError(CalculoError):
    """El porcentaje de descuento especificado es inválido."""
    def __init__(self, descuento):
        super().__init__(
            f"Descuento '{descuento}%' inválido. Debe ser un valor entre 0 y 100."
        )
        self.codigo = "ERR_CALCULO_DESCUENTO_INVALIDO"


class ImpuestoInvalidoError(CalculoError):
    """La tasa de impuesto especificada es inválida."""
    def __init__(self, impuesto):
        super().__init__(
            f"Tasa de impuesto '{impuesto}%' inválida. Debe ser un valor no negativo."
        )
        self.codigo = "ERR_CALCULO_IMPUESTO_INVALIDO"
