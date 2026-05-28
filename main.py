import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from login import login
from Componentes.catalogo import ComponenteCatalogo
from Componentes.reserva import ComponenteLogicaReserva, ComponenteSeleccionAsientos
from Agentes.buscador_vuelos import DataLoaderAgent, FlightSearchAgent, SeatBlockingAgent, InterfaceAgent
from Agentes.AgenteCierreVentas import AgenteCierreVentas
from Aspectos.alertas import alert_aspect


def main():
    # 1. Login
    passenger_name = login()

    # 2. Agente buscador — cargar datos y filtrar destinos disponibles
    flights = DataLoaderAgent.load_flights()
    seats_idx = DataLoaderAgent.load_seats(flights)
    blocking_agent = SeatBlockingAgent(seats_idx, flights)
    search_agent = FlightSearchAgent(flights, blocking_agent)

    print("\n================================")
    print("  DESTINOS DISPONIBLES:")
    print("================================")
    destinos = search_agent.get_known_destinations("BUENOS AIRES")
    for i, d in enumerate(destinos, 1):
        print(f"  {i}. {d}")

    while True:
        try:
            idx = int(input("\nElegí el número del destino: ")) - 1
            if 0 <= idx < len(destinos):
                destination = destinos[idx]
                break
            print("[Error] Opción fuera de rango.")
        except ValueError:
            print("[Error] Ingresá un número válido.")

    # 3. Catálogo — mostrar vuelos del destino elegido y seleccionar
    catalogo = ComponenteCatalogo()
    catalogo.vuelos = [v for v in catalogo.vuelos if v["destino"] == destination]
    catalogo.mostrar_catalogo()
    datos = catalogo.seleccionar_y_preparar_json()

    if not datos:
        print("[Error] No se pudo seleccionar un vuelo.")
        return

    flight_id = datos["id_vuelo"]

    # 4. Sistema de reserva — mapa de asientos + confirmar (con alertas)
    @alert_aspect(
        start_message=f"Iniciando reserva en vuelo {flight_id}...",
        success_message="Reserva realizada correctamente",
        error_message="No se pudo realizar la reserva"
    )
    def hacer_reserva(passenger_name):
        # Recargar datos frescos para que el mapa refleje el estado actual
        flights_now = DataLoaderAgent.load_flights()
        seats_now = DataLoaderAgent.load_seats(flights_now)
        blocker_now = SeatBlockingAgent(seats_now, flights_now)
        ui = InterfaceAgent(
            FlightSearchAgent(flights_now, blocker_now),
            blocker_now,
            seats_now
        )
        ui._print_seat_map(flight_id)

        logica = ComponenteLogicaReserva()
        seleccion = ComponenteSeleccionAsientos(logica)
        seleccion.seleccionar_asiento_vuelo(flight_id, passenger_name)

    hacer_reserva(passenger_name)

    # 5. Agente de cierre — verificar si el vuelo quedó sin asientos
    AgenteCierreVentas().ejecutar()

    print(f"\n¡Hasta pronto, {passenger_name}!")


if __name__ == "__main__":
    main()
