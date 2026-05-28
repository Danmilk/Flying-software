import json
import os

class ComponenteCatalogo:
    def __init__(self):
        # Obtener la ruta absoluta del archivo flights.json en el mismo directorio del script
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_flights = os.path.join(dir_actual, "..", "data", "flights.json")
        
        try:
            with open(ruta_flights, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Mapeamos los campos de flights.json al formato usado por el catálogo
            self.vuelos = []
            for item in data:
                self.vuelos.append({
                    "id_vuelo": item.get("id"),
                    "fecha_salida": item.get("date"),
                    "origen": item.get("origin"),
                    "destino": item.get("destination")
                })
        except Exception as e:
            print(f"[Error] No se pudo cargar el archivo flights.json: {e}")
            self.vuelos = []

    def mostrar_catalogo(self):
        """Despliega los vuelos disponibles con los 4 datos requeridos"""
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
            print("-" * 41)

    def seleccionar_y_preparar_json(self):
        """Permite elegir el vuelo, ingresar asiento y genera el JSON de salida"""
        if not self.vuelos:
            print("[Error] No hay vuelos cargados en el catálogo.")
            return

        try:
            # 1. Selección del vuelo desde el catálogo
            opcion = int(input("\nSeleccione el número de vuelo (ej. 1, 2, ...): ")) - 1
            
            if opcion < 0 or opcion >= len(self.vuelos):
                print("[Error] Selección fuera de rango.")
                return

            vuelo_elegido = self.vuelos[opcion]["id_vuelo"]

            # 2. Entrada de datos de ubicación (Fila y Columna)
            fila = input("Ingrese la fila del asiento: ")
            columna = input("Ingrese la columna del asiento: ")

            # 3. Estructuración de los datos requeridos para Reserva
            datos_preparados = {
                "id_vuelo": vuelo_elegido,
                "fila": fila,
                "columna": columna
            }

            # 4. Conversión estricta a formato JSON (String estructurado)
            json_resultado = json.dumps(datos_preparados, indent=4)
            
            # Guardar el JSON en un archivo reserva.json en el mismo directorio
            dir_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_reserva = os.path.join(dir_actual, "..", "data", "reserva.json")
            with open(ruta_reserva, "w", encoding="utf-8") as f:
                f.write(json_resultado)

            # 5. Mostrar el artefacto final generado por este componente
            print("\n" + "="*45)
            print(" [COMPONENTE CATÁLOGO] -> JSON PREPARADO Y GUARDADO:")
            print("="*45)
            print(json_resultado)
            print("="*45)
            print(f"*(Guardado en: {ruta_reserva})*")
            print("*(Listo para ser consumido por el componente Reserva)*\n")

            return datos_preparados

        except ValueError:
            print("[Error] Por favor, introduzca un número válido.")

# ========================================================
# INICIO DE LA APLICACIÓN (CONSOLA)
# ========================================================
if __name__ == "__main__":
    componente = ComponenteCatalogo()
    
    # Paso 1: Ver el catálogo
    componente.mostrar_catalogo()
    
    # Paso 2: Seleccionar y estructurar los datos de salida
    componente.seleccionar_y_preparar_json()