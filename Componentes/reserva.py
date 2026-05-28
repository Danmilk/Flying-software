import json
import os


class ComponenteLogicaReserva:
    """Este es el componente aparte al que se le enviarán los datos."""
    def recibir_datos_seleccion(self, flight_id: str, fila: str, columna: str):
        print("\n" + "="*45)
        print(" [COMPONENTE LÓGICA] -> DATOS RECIBIDOS CON ÉXITO:")
        print("="*45)
        print(f" Vuelo ID : {flight_id}")
        print(f" Fila     : {fila}")
        print(f" Columna  : {columna}")
        print("=========================================")
        print("*(Aquí es donde este módulo aparte procesará la escritura)*\n")



# COMPONENTE DE SELECCIÓN (Lee, muestra, captura y envía)

class ComponenteSeleccionAsientos:
    def __init__(self, componente_logica):
        # Inyección de dependencia: recibe el componente al que le enviará los datos
        self.componente_logica = componente_logica
        
        # Ruta absoluta hacia la carpeta data/seats.json
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        self.ruta_seats = os.path.join(dir_actual, "data", "seats.json")

    def _cargar_asientos(self) -> list:
        """Solo lee el archivo JSON de asientos."""
        if not os.path.exists(self.ruta_seats):
            print(f"[Error] No se encontró el archivo maestro en: {self.ruta_seats}")
            return []
        try:
            with open(self.ruta_seats, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Fallo al leer seats.json: {e}")
            return []

    def seleccionar_asiento_vuelo(self, flight_id: str):
        """Muestra los asientos del vuelo y solicita la selección por consola."""
        todos_los_asientos = self._cargar_asientos()
        
        # 1. Filtrar los asientos pertenecientes al vuelo recibido
        asientos_vuelo = [s for s in todos_los_asientos if s.get("flight_id") == flight_id]

        if not asientos_vuelo:
            print(f"[Error] No se encontraron asientos registrados para el vuelo: {flight_id}")
            return

        # 2. Desplegar los asientos en consola
        print("\n=========================================")
        print(f"        MAPA DE ASIENTOS - VUELO {flight_id}      ")
        print("=========================================")
        for s in asientos_vuelo:
            estado = "🔴 Ocupado" if s.get("ocupado") else "🟢 Disponible"
            print(f" Fila: {s.get('fila')} | Columna: {s.get('columna')} | Estado: {estado}")
        print("=========================================")

        # 3. Solicitar la selección al usuario
        fila_elegida = input("Seleccione el número de Fila: ").strip()
        columna_elegida = input("Seleccione la letra de Columna: ").strip().upper()

        # 4. Validar existencia y disponibilidad localmente
        asiento_valido = next(
            (s for s in asientos_vuelo if str(s.get("fila")) == fila_elegida and s.get("columna", "").upper() == columna_elegida), 
            None
        )

        if not asiento_valido:
            print("[Error] El asiento ingresado no existe para este vuelo.")
            return

        if asiento_valido.get("ocupado"):
            print("[Error] El asiento seleccionado ya se encuentra ocupado.")
            return

        # 5. PASAR LOS DATOS AL OTRO COMPONENTE ENCARGADO DE LA LÓGICA
        self.componente_logica.recibir_datos_seleccion(
            flight_id=flight_id, 
            fila=fila_elegida, 
            columna=columna_elegida
        )


# =====================================================================
# PRUEBA DE ARQUITECTURA
# =====================================================================
if __name__ == "__main__":
    # 1. Creamos el componente de lógica que recibirá la información
    modulo_logica = ComponenteLogicaReserva()
    
    # 2. Creamos el componente de selección pasándole el módulo destino
    modulo_seleccion = ComponenteSeleccionAsientos(componente_logica=modulo_logica)
    
    # Simulación: Recibe el ID de vuelo (por ejemplo, el que viene de tu catálogo)
    vuelo_recibido = "FL001" 
    
    # Arrancamos el flujo del componente
    modulo_seleccion.seleccionar_asiento_vuelo(vuelo_recibido)
