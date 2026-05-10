"""
main.py
=======
Punto de entrada del Sistema Integral de Gestión — Software FJ.

Simula 12 operaciones completas que cubren:
    ✔ Clientes válidos e inválidos
    ✔ Servicios correctos e incorrectos
    ✔ Reservas exitosas y fallidas
    ✔ Confirmación, procesamiento y cancelación
    ✔ Manejo robusto de excepciones en cada etapa
    ✔ Registro de todos los eventos en sistema_fj.log
"""

import os
import sys

# Asegurar que Python encuentre todos los módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import log
from entidades import Cliente, RepositorioClientes
from servicios import (
    ReservaSala,
    AlquilerEquipo,
    AsesoriaEspecializada,
    CatalogoServicios,
)
from reservas import GestorReservas, EstadoReserva
from excepciones import (
    SistemaFJError,
    DatosClienteInvalidosError,
    ClienteYaExisteError,
    ParametrosServicioInvalidosError,
    ServicioNoDisponibleError,
    CapacidadExcedidaError,
    DuracionInvalidaError,
    ReservaYaConfirmadaError,
    ReservaCanceladaError,
    DescuentoInvalidoError,
)


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE PRESENTACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def titulo(texto: str):
    linea = "─" * 68
    print(f"\n{linea}\n  {texto}\n{linea}")


def subtitulo(texto: str):
    print(f"\n  ▸ {texto}")


def mostrar_desglose(desglose: dict):
    print()
    for k, v in desglose.items():
        if isinstance(v, float):
            print(f"    {k:<20}: $ {v:>14,.2f} COP")
        else:
            print(f"    {k:<20}: {v}")


def separador():
    print()


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 1 — Registrar clientes válidos
# ══════════════════════════════════════════════════════════════════════════════

def op1_registrar_clientes(repo: RepositorioClientes):
    titulo("OPERACIÓN 1 — Registro de clientes válidos")
    datos = [
        ("Laura", "Gómez",    "lgomez@empresa.com",    "+57 311 2345678", "vip"),
        ("Carlos", "Ramírez", "c.ramirez@correo.co",   "+57 300 9876543", "empresarial"),
        ("Sofía",  "Torres",  "sofia.torres@mail.com", "+57 320 1111222", "regular"),
    ]
    clientes = []
    for nombre, apellido, correo, tel, tipo in datos:
        try:
            c = Cliente(nombre, apellido, correo, tel, tipo)
            repo.agregar(c)
            print(f"  ✔ Cliente registrado: {c.nombre_completo} [{c.id}]")
            clientes.append(c)
        except SistemaFJError as exc:
            log.error(str(exc), "OP1")
            print(f"  ✖ Error: {exc}")
    return clientes


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 2 — Intentar registrar clientes INVÁLIDOS
# ══════════════════════════════════════════════════════════════════════════════

def op2_clientes_invalidos(repo: RepositorioClientes, clientes: list):
    titulo("OPERACIÓN 2 — Clientes con datos inválidos (errores controlados)")

    casos = [
        # (descripción, args)
        ("Nombre vacío",
         dict(nombre="", apellido="Pérez", correo="x@x.com",
              telefono="+57 300 0000000", tipo_cliente="regular")),
        ("Correo malformado",
         dict(nombre="Ana", apellido="Pérez", correo="no-es-correo",
              telefono="+57 300 0000000", tipo_cliente="regular")),
        ("Tipo de cliente inválido",
         dict(nombre="Juan", apellido="López", correo="jlopez@test.com",
              telefono="+57 300 1234567", tipo_cliente="platino")),
        ("Teléfono demasiado corto",
         dict(nombre="María", apellido="Ruiz", correo="mruiz@test.com",
              telefono="123", tipo_cliente="regular")),
    ]

    for desc, kwargs in casos:
        subtitulo(desc)
        try:
            c = Cliente(**kwargs)
            repo.agregar(c)
        except DatosClienteInvalidosError as exc:
            print(f"  ✖ DatosClienteInvalidosError: {exc}")
        except SistemaFJError as exc:
            print(f"  ✖ {type(exc).__name__}: {exc}")

    # Intentar duplicar un cliente existente
    subtitulo("Correo duplicado")
    try:
        if clientes:
            c_dup = Cliente(
                "Laura", "Copia",
                clientes[0].correo,   # mismo correo que el primer cliente
                "+57 300 9999999",
                "regular"
            )
            repo.agregar(c_dup)
    except ClienteYaExisteError as exc:
        print(f"  ✖ ClienteYaExisteError: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 3 — Crear catálogo de servicios válidos
# ══════════════════════════════════════════════════════════════════════════════

def op3_crear_servicios(catalogo: CatalogoServicios):
    titulo("OPERACIÓN 3 — Creación de servicios válidos")
    servicios = []

    try:
        sala1 = ReservaSala(
            nombre="Sala Innovación",
            descripcion="Sala de reuniones para hasta 20 personas, equipada con tecnología AV.",
            precio_base_hora=80_000,
            aforo=20,
            equipada=True,
            capacidad_max=3,
        )
        catalogo.agregar(sala1)
        print(f"  ✔ {sala1.nombre} [{sala1.id}]")
        servicios.append(sala1)
    except SistemaFJError as exc:
        log.error(str(exc), "OP3"); print(f"  ✖ {exc}")

    try:
        equipo1 = AlquilerEquipo(
            nombre="Laptop Dell XPS",
            descripcion="Laptop de alto rendimiento para desarrollo y diseño.",
            precio_base_hora=15_000,
            tipo_equipo="laptop",
            deposito=500_000,
            unidades_disp=5,
            capacidad_max=5,
        )
        catalogo.agregar(equipo1)
        print(f"  ✔ {equipo1.nombre} [{equipo1.id}]")
        servicios.append(equipo1)
    except SistemaFJError as exc:
        log.error(str(exc), "OP3"); print(f"  ✖ {exc}")

    try:
        asesoria1 = AsesoriaEspecializada(
            nombre="Consultoría Arquitectura Cloud",
            descripcion="Asesoría en diseño e implementación de arquitecturas en la nube.",
            precio_base_hora=250_000,
            area="Tecnología Cloud",
            nivel_experto="principal",
            capacidad_max=2,
        )
        catalogo.agregar(asesoria1)
        print(f"  ✔ {asesoria1.nombre} [{asesoria1.id}]")
        servicios.append(asesoria1)
    except SistemaFJError as exc:
        log.error(str(exc), "OP3"); print(f"  ✖ {exc}")

    return servicios


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 4 — Intentar crear servicios INVÁLIDOS
# ══════════════════════════════════════════════════════════════════════════════

def op4_servicios_invalidos(catalogo: CatalogoServicios):
    titulo("OPERACIÓN 4 — Servicios con parámetros inválidos")

    subtitulo("Precio base negativo en ReservaSala")
    try:
        s = ReservaSala("Sala X", "desc", precio_base_hora=-5000, aforo=10)
        catalogo.agregar(s)
    except ParametrosServicioInvalidosError as exc:
        print(f"  ✖ ParametrosServicioInvalidosError: {exc}")

    subtitulo("Tipo de equipo desconocido en AlquilerEquipo")
    try:
        e = AlquilerEquipo(
            "Dron Industrial", "desc", 20_000,
            tipo_equipo="dron",   # inválido
            deposito=300_000
        )
        catalogo.agregar(e)
    except ParametrosServicioInvalidosError as exc:
        print(f"  ✖ ParametrosServicioInvalidosError: {exc}")

    subtitulo("Nivel de experto inexistente en AsesoriaEspecializada")
    try:
        a = AsesoriaEspecializada(
            "Asesoría X", "desc", 100_000,
            area="Marketing",
            nivel_experto="guru"   # inválido
        )
        catalogo.agregar(a)
    except ParametrosServicioInvalidosError as exc:
        print(f"  ✖ ParametrosServicioInvalidosError: {exc}")

    subtitulo("Aforo cero en ReservaSala")
    try:
        s2 = ReservaSala("Sala Y", "desc", 50_000, aforo=0)
        catalogo.agregar(s2)
    except ParametrosServicioInvalidosError as exc:
        print(f"  ✖ ParametrosServicioInvalidosError: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 5 — Calcular costos con el método sobrecargado
# ══════════════════════════════════════════════════════════════════════════════

def op5_calculos_costo(servicios: list, clientes: list):
    titulo("OPERACIÓN 5 — Cálculos de costo con parámetros opcionales")

    sala, equipo, asesoria = servicios[0], servicios[1], servicios[2]
    cli_vip = clientes[0]       # descuento VIP 20 %
    cli_emp = clientes[1]       # descuento empresarial 10 %

    subtitulo(f"ReservaSala — 3 horas, {cli_vip.tipo_cliente} (-20%), 8 personas")
    try:
        d = sala.calcular_costo_con_extras(
            horas=3,
            descuento=cli_vip.descuento_por_tipo(),
            personas=8,
        )
        mostrar_desglose(d)
    except SistemaFJError as exc:
        print(f"  ✖ {exc}")

    subtitulo(f"AlquilerEquipo — 48 horas, 2 unidades, con depósito, descuento 10%")
    try:
        d = equipo.calcular_costo_con_extras(
            horas=48,
            descuento=cli_emp.descuento_por_tipo(),
            unidades=2,
            incluir_deposito=True,
        )
        mostrar_desglose(d)
    except SistemaFJError as exc:
        print(f"  ✖ {exc}")

    subtitulo("AsesoriaEspecializada — 4h, urgente, con informe escrito")
    try:
        d = asesoria.calcular_costo_con_extras(
            horas=4,
            descuento=0.0,
            urgente=True,
            informe_escrito=True,
        )
        mostrar_desglose(d)
    except SistemaFJError as exc:
        print(f"  ✖ {exc}")

    subtitulo("Cálculo con descuento inválido (>100%)")
    try:
        sala.calcular_costo_con_extras(horas=2, descuento=110.0)
    except DescuentoInvalidoError as exc:
        print(f"  ✖ DescuentoInvalidoError: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 6 — Crear y confirmar reservas válidas
# ══════════════════════════════════════════════════════════════════════════════

def op6_reservas_exitosas(gestor: GestorReservas, clientes: list, servicios: list):
    titulo("OPERACIÓN 6 — Creación y confirmación de reservas exitosas")

    sala, equipo, asesoria = servicios[0], servicios[1], servicios[2]
    reservas_creadas = []

    # Reserva 1: sala para cliente VIP
    subtitulo("Reserva sala — cliente VIP, 4 horas, 10 personas")
    try:
        r1 = gestor.crear(
            cliente=clientes[0],
            servicio=sala,
            duracion_horas=4,
            notas="Reunión de directivos",
            personas=10,
        )
        r1.confirmar()
        print(f"  ✔ {r1.describir()}")
        reservas_creadas.append(r1)
    except SistemaFJError as exc:
        log.error(str(exc), "OP6"); print(f"  ✖ {exc}")

    # Reserva 2: equipo para cliente empresarial
    subtitulo("Reserva equipo — cliente empresarial, 24 horas, 3 laptops")
    try:
        r2 = gestor.crear(
            cliente=clientes[1],
            servicio=equipo,
            duracion_horas=24,
            notas="Hackathon interno",
            unidades=3,
            incluir_deposito=True,
        )
        r2.confirmar()
        print(f"  ✔ {r2.describir()}")
        reservas_creadas.append(r2)
    except SistemaFJError as exc:
        log.error(str(exc), "OP6"); print(f"  ✖ {exc}")

    # Reserva 3: asesoría para cliente regular
    subtitulo("Reserva asesoría — cliente regular, 2 horas, urgente + informe")
    try:
        r3 = gestor.crear(
            cliente=clientes[2],
            servicio=asesoria,
            duracion_horas=2,
            notas="Revisión de infraestructura cloud",
            urgente=True,
            informe_escrito=True,
        )
        r3.confirmar()
        print(f"  ✔ {r3.describir()}")
        reservas_creadas.append(r3)
    except SistemaFJError as exc:
        log.error(str(exc), "OP6"); print(f"  ✖ {exc}")

    return reservas_creadas


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 7 — Intentar confirmar la misma reserva dos veces
# ══════════════════════════════════════════════════════════════════════════════

def op7_doble_confirmacion(reservas: list):
    titulo("OPERACIÓN 7 — Doble confirmación de reserva (error controlado)")
    if not reservas:
        print("  ⚠ No hay reservas para probar.")
        return
    r = reservas[0]
    subtitulo(f"Confirmando por segunda vez la reserva [{r.id}]")
    try:
        r.confirmar()
    except ReservaYaConfirmadaError as exc:
        print(f"  ✖ ReservaYaConfirmadaError: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 8 — Crear reservas con parámetros inválidos
# ══════════════════════════════════════════════════════════════════════════════

def op8_reservas_invalidas(gestor: GestorReservas, clientes: list, servicios: list):
    titulo("OPERACIÓN 8 — Reservas con datos inválidos (errores controlados)")
    sala, equipo, asesoria = servicios[0], servicios[1], servicios[2]

    subtitulo("Duración cero horas")
    try:
        r = gestor.crear(clientes[0], sala, duracion_horas=0)
        r.confirmar()
    except DuracionInvalidaError as exc:
        print(f"  ✖ DuracionInvalidaError: {exc}")

    subtitulo("Duración negativa")
    try:
        r = gestor.crear(clientes[1], equipo, duracion_horas=-5)
        r.confirmar()
    except DuracionInvalidaError as exc:
        print(f"  ✖ DuracionInvalidaError: {exc}")

    subtitulo("Personas exceden el aforo de la sala")
    try:
        r = gestor.crear(
            clientes[2], sala, duracion_horas=2,
            personas=999   # sala tiene aforo 20
        )
        r.confirmar()
    except (ParametrosServicioInvalidosError, SistemaFJError) as exc:
        print(f"  ✖ {type(exc).__name__}: {exc}")

    subtitulo("Unidades de equipo superiores al inventario")
    try:
        r = gestor.crear(
            clientes[0], equipo, duracion_horas=8,
            unidades=100   # solo hay 5
        )
        r.confirmar()
    except (ParametrosServicioInvalidosError, SistemaFJError) as exc:
        print(f"  ✖ {type(exc).__name__}: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 9 — Cancelar y procesar reservas
# ══════════════════════════════════════════════════════════════════════════════

def op9_cancelar_y_procesar(reservas: list, gestor: GestorReservas,
                             clientes: list, servicios: list):
    titulo("OPERACIÓN 9 — Cancelación y procesamiento de reservas")

    sala = servicios[0]

    # Cancelar la primera reserva confirmada
    if reservas:
        r = reservas[0]
        subtitulo(f"Cancelando reserva [{r.id}]")
        try:
            r.cancelar(motivo="El cliente solicitó reprogramar.")
            print(f"  ✔ Estado actual: {r.estado.value}")
        except SistemaFJError as exc:
            print(f"  ✖ {exc}")

        # Intentar cancelar de nuevo (ya cancelada)
        subtitulo("Intentar cancelar una reserva ya cancelada")
        try:
            r.cancelar()
        except ReservaCanceladaError as exc:
            print(f"  ✖ ReservaCanceladaError: {exc}")

    # Procesar (completar) la segunda reserva
    if len(reservas) >= 2:
        r2 = reservas[1]
        subtitulo(f"Procesando (completando) reserva [{r2.id}]")
        try:
            r2.procesar()
            print(f"  ✔ Estado actual: {r2.estado.value}")
        except SistemaFJError as exc:
            print(f"  ✖ {exc}")

        # Intentar procesar de nuevo (ya completada)
        subtitulo("Procesar una reserva ya completada")
        try:
            r2.procesar()
        except ValueError as exc:
            print(f"  ✖ ValueError: {exc}")

    # Nueva reserva para demostrar disponibilidad recuperada
    subtitulo("Crear nueva reserva en sala liberada tras cancelación")
    try:
        r_nueva = gestor.crear(
            cliente=clientes[2],
            servicio=sala,
            duracion_horas=1,
            notas="Nueva reserva tras cancelación",
            personas=5,
        )
        r_nueva.confirmar()
        print(f"  ✔ {r_nueva.describir()}")
    except SistemaFJError as exc:
        log.error(str(exc), "OP9"); print(f"  ✖ {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 10 — Probar capacidad máxima del servicio
# ══════════════════════════════════════════════════════════════════════════════

def op10_capacidad_maxima(gestor: GestorReservas, clientes: list, servicios: list):
    titulo("OPERACIÓN 10 — Verificar límite de capacidad del servicio")

    # La asesoría tiene capacidad_max=2; ya hay 1 reserva activa (de OP6).
    asesoria = servicios[2]
    print(f"  Capacidad asesoría: {asesoria.reservas_activas}/{asesoria.capacidad_max} ocupadas")

    # Segunda reserva (llena la capacidad)
    subtitulo("Segunda reserva de asesoría (ocupa el último cupo)")
    try:
        r = gestor.crear(
            clientes[1], asesoria, duracion_horas=1,
            urgente=False, informe_escrito=False
        )
        r.confirmar()
        print(f"  ✔ Reserva [{r.id}] confirmada. Ocupadas: {asesoria.reservas_activas}/{asesoria.capacidad_max}")
    except SistemaFJError as exc:
        print(f"  ✖ {exc}")

    # Tercera reserva (debe fallar por capacidad)
    subtitulo("Tercera reserva de asesoría (debe fallar — sin cupos)")
    try:
        r2 = gestor.crear(
            clientes[0], asesoria, duracion_horas=1,
            urgente=False, informe_escrito=False
        )
        r2.confirmar()
        print(f"  ✔ Reserva [{r2.id}] confirmada.")
    except CapacidadExcedidaError as exc:
        print(f"  ✖ CapacidadExcedidaError: {exc}")
    except SistemaFJError as exc:
        print(f"  ✖ {type(exc).__name__}: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 11 — Deshabilitar un servicio e intentar reservarlo
# ══════════════════════════════════════════════════════════════════════════════

def op11_servicio_deshabilitado(gestor: GestorReservas, clientes: list, servicios: list):
    titulo("OPERACIÓN 11 — Reserva sobre servicio deshabilitado")
    sala = servicios[0]

    sala.deshabilitar("Mantenimiento programado.")
    print(f"  Disponibilidad sala: {sala.disponible}")

    subtitulo("Intentar reservar sala deshabilitada")
    try:
        r = gestor.crear(clientes[0], sala, duracion_horas=2, personas=5)
        r.confirmar()
    except ServicioNoDisponibleError as exc:
        print(f"  ✖ ServicioNoDisponibleError: {exc}")
    finally:
        sala.habilitar()
        print(f"  Sala rehabilitada. Disponible: {sala.disponible}")


# ══════════════════════════════════════════════════════════════════════════════
# OPERACIÓN 12 — Resumen final del sistema
# ══════════════════════════════════════════════════════════════════════════════

def op12_resumen(repo: RepositorioClientes, catalogo: CatalogoServicios,
                 gestor: GestorReservas):
    titulo("OPERACIÓN 12 — Resumen final del sistema")

    print(f"\n  Clientes registrados : {repo.total()}")
    for c in repo.listar():
        print(f"    [{c.id}] {c.nombre_completo} — {c.tipo_cliente.upper()} "
              f"| Reservas: {len(c.reservas_ids)}")

    print(f"\n  Servicios en catálogo : {catalogo.total()}")
    for s in catalogo.listar():
        disp = "✔" if s.disponible else "✘"
        print(f"    [{s.id}] {s.nombre} ({s.__class__.__name__}) "
              f"| {disp} | {s.reservas_activas}/{s.capacidad_max}")

    print(f"\n  Reservas totales : {gestor.total()}")
    for estado in EstadoReserva:
        rs = gestor.listar_por_estado(estado)
        if rs:
            print(f"    {estado.value:<12}: {len(rs)}")

    print()
    log.info("Sesión de demostración finalizada exitosamente.", "Main")


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 68)
    print("   SOFTWARE FJ — Sistema Integral de Gestión")
    print("   Módulos: Clientes | Servicios | Reservas")
    print("═" * 68)

    # Instanciar repositorios
    repo_clientes = RepositorioClientes()
    catalogo      = CatalogoServicios()
    gestor        = GestorReservas()

    # Ejecutar operaciones en secuencia
    clientes  = op1_registrar_clientes(repo_clientes)
    op2_clientes_invalidos(repo_clientes, clientes)
    servicios = op3_crear_servicios(catalogo)
    op4_servicios_invalidos(catalogo)
    op5_calculos_costo(servicios, clientes)
    reservas  = op6_reservas_exitosas(gestor, clientes, servicios)
    op7_doble_confirmacion(reservas)
    op8_reservas_invalidas(gestor, clientes, servicios)
    op9_cancelar_y_procesar(reservas, gestor, clientes, servicios)
    op10_capacidad_maxima(gestor, clientes, servicios)
    op11_servicio_deshabilitado(gestor, clientes, servicios)
    op12_resumen(repo_clientes, catalogo, gestor)

    print("\n  ✔ Todas las operaciones completadas. "
          "Revise 'sistema_fj.log' para el registro completo.")
    print("═" * 68 + "\n")


if __name__ == "__main__":
    main()
