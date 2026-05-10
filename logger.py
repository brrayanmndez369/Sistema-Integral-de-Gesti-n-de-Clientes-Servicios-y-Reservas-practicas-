"""
logger.py
=========
Módulo de registro de eventos y errores del Sistema Integral de Gestión
de Software FJ.

Toda excepción y evento relevante queda registrado en 'sistema_fj.log'
con marca de tiempo, nivel de severidad y contexto de operación.
"""

import os
import traceback
from datetime import datetime
from enum import Enum


class Nivel(Enum):
    INFO    = "INFO"
    AVISO   = "AVISO"
    ERROR   = "ERROR"
    CRITICO = "CRITICO"


class Logger:
    """
    Registrador de eventos singleton que escribe en un archivo de log.
    Se puede usar como Logger() en cualquier módulo; siempre apunta
    a la misma instancia.
    """

    _instancia = None
    _archivo_log: str = "sistema_fj.log"

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    # ── Inicialización ────────────────────────────────────────────────────────

    def _inicializar(self):
        """Prepara el archivo de log y escribe la cabecera de sesión."""
        self._ruta = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self._archivo_log
        )
        self._escribir_cabecera()

    def _escribir_cabecera(self):
        separador = "=" * 72
        encabezado = (
            f"\n{separador}\n"
            f"  SOFTWARE FJ — Sistema Integral de Gestión\n"
            f"  Sesión iniciada: {self._marca_tiempo()}\n"
            f"{separador}\n"
        )
        try:
            with open(self._ruta, "a", encoding="utf-8") as f:
                f.write(encabezado)
        except OSError:
            # Si no se puede escribir el log, el sistema sigue en pie.
            pass

    # ── API pública ───────────────────────────────────────────────────────────

    def info(self, mensaje: str, contexto: str = ""):
        self._registrar(Nivel.INFO, mensaje, contexto)

    def aviso(self, mensaje: str, contexto: str = ""):
        self._registrar(Nivel.AVISO, mensaje, contexto)

    def error(self, mensaje: str, contexto: str = "", exc: Exception = None):
        self._registrar(Nivel.ERROR, mensaje, contexto, exc)

    def critico(self, mensaje: str, contexto: str = "", exc: Exception = None):
        self._registrar(Nivel.CRITICO, mensaje, contexto, exc)

    # ── Internos ──────────────────────────────────────────────────────────────

    @staticmethod
    def _marca_tiempo() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _registrar(
        self,
        nivel: Nivel,
        mensaje: str,
        contexto: str = "",
        exc: Exception = None,
    ):
        ctx = f" [{contexto}]" if contexto else ""
        linea = f"{self._marca_tiempo()} | {nivel.value:<7}{ctx} | {mensaje}\n"

        # Si viene una excepción, agrega el traceback
        if exc is not None:
            tb = traceback.format_exc()
            if tb and tb.strip() != "NoneType: None":
                linea += f"  → {tb.strip()}\n"
            elif str(exc):
                linea += f"  → {type(exc).__name__}: {exc}\n"

        # Imprimir en consola según gravedad
        prefijos = {
            Nivel.INFO:    "  ℹ",
            Nivel.AVISO:   "  ⚠",
            Nivel.ERROR:   "  ✖",
            Nivel.CRITICO: "  ☠",
        }
        print(f"{prefijos[nivel]} {nivel.value:<7}{ctx}: {mensaje}")

        # Escribir en archivo
        try:
            with open(self._ruta, "a", encoding="utf-8") as f:
                f.write(linea)
        except OSError:
            pass  # No detener el sistema por un fallo de escritura


# Instancia global para importar directamente
log = Logger()
