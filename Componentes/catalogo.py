import json
import os

class ComponenteCatalogo:
    def __init__(self):
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_flights = os.path.join(dir_actual, "..", "data", "flights.json")

        try:
            with open(ruta_flights, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.vuelos = []
            for item in data:
                if item.get("seats_available", 0) > 0:
                    self.vuelos.append({
                        "id_vuelo": item.get("id"),
                        "fecha_salida": item.get("date"),
                        "origen": item.get("origin"),
                        "destino": item.get("destination"),
                        "asientos_disponibles": item.get("seats_available")
                    })
        except Exception as e:
            print(f"[Error] No se pudo cargar el archivo flights.json: {e}")
            self.vuelos = []

    def mostrar_catalogo(self):
        print("\n=========================================")
        print("       CATÁLOGO DE VUELOS DISPONIBLES    ")
        print("=========================================")
        if not self.vuelos:
            print(" No hay vuelos disponibles cargados.")
            print("=========================================")
            return

        for i, vuelo in enumerate(self.vuelos, start=1):
            print(f"[{i}] VUELO: {vuelo['id_vuelo']}")
            print(f"    Fecha de Salida: {vuelo['fecha_salida']}")
            print(f"    Origen:          {vuelo['origen']}")
            print(f"    Destino:         {vuelo['destino']}")
            print(f"    Asientos libres: {vuelo['asientos_disponibles']}")
            print("-" * 41)

    def seleccionar_y_preparar_json(self):
        if not self.vuelos:
            print("[Error] No hay vuelos cargados en el catálogo.")
            return None

        try:
            opcion = int(input("\nSeleccione el número de vuelo (ej. 1, 2, ...): ")) - 1

            if opcion < 0 or opcion >= len(self.vuelos):
                print("[Error] Selección fuera de rango.")
                return None

            vuelo_elegido = self.vuelos[opcion]["id_vuelo"]
            print(f"\n[CATÁLOGO] Vuelo seleccionado: {vuelo_elegido}")
            return {"id_vuelo": vuelo_elegido}

        except ValueError:
            print("[Error] Por favor, introduzca un número válido.")
            return None
