import json
import os

class AgenteCierreVentas:
    def __init__(self):
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        self.ruta_seats = os.path.join(dir_actual, "data", "seats.json")
        self.ruta_flights = os.path.join(dir_actual, "data", "flights.json")

    def ejecutar(self):
        with open(self.ruta_seats, "r", encoding="utf-8") as f:
            seats = json.load(f)

        with open(self.ruta_flights, "r", encoding="utf-8") as f:
            flights = json.load(f)

        for vuelo in flights:
            flight_id = vuelo["id"]

            ocupados = [
                asiento for asiento in seats
                if asiento["flight_id"] == flight_id and asiento["ocupado"] == 1
            ]

            if len(ocupados) >= int(vuelo["seats_available"]):
                vuelo["status"] = "CLOSED"

        with open(self.ruta_flights, "w", encoding="utf-8") as f:
            json.dump(flights, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    agente = AgenteCierreVentas()
    agente.ejecutar()