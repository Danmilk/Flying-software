import json
import os
from Aspectos.alertas import alert_aspect

class AgenteCierreVentas:
    def __init__(self):
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        self.ruta_seats = os.path.join(dir_actual, "..", "data", "seats.json")
        self.ruta_flights = os.path.join(dir_actual, "..", "data", "flights.json")

    @alert_aspect(
        start_message="Verificando estado de vuelos...",
        success_message="Verificación de cierre completada",
        error_message="Error al verificar cierre de vuelos"
    )
    def ejecutar(self):
        with open(self.ruta_seats, "r", encoding="utf-8") as f:
            seats = json.load(f)

        with open(self.ruta_flights, "r", encoding="utf-8") as f:
            flights = json.load(f)

        cerrados = []
        for vuelo in flights:
            flight_id = vuelo["id"]

            total = sum(1 for s in seats if s["flight_id"] == flight_id)
            ocupados = sum(1 for s in seats if s["flight_id"] == flight_id and s["ocupado"])

            if total > 0:
                vuelo["seats_available"] = total - ocupados
                if vuelo["seats_available"] == 0:
                    cerrados.append(flight_id)

        with open(self.ruta_flights, "w", encoding="utf-8") as f:
            json.dump(flights, f, indent=4, ensure_ascii=False)

        if cerrados:
            print(f"Vuelos cerrados por capacidad completa: {', '.join(cerrados)}")
