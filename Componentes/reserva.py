import json
import os
from Aspectos.logging_aspect import audit_logging_aspect

# =====================================================================
# COMPONENTE RECEPTOR (El otro módulo que manejará la lógica/escritura)
# =====================================================================
class ComponenteLogicaReserva:
    """Este es el componente aparte al que se le enviarán los datos."""
    @audit_logging_aspect
    def recibir_datos_seleccion(self, flight_id: str, fila: str, columna: str, passenger_name: str = ""):
        from Aspectos.bloqueo import lock_seat
        result = lock_seat(flight_id, fila, columna, passenger_name)
        print(result["message"])
        return result


# =====================================================================
# COMPONENTE DE SELECCIÓN (Lee, muestra, captura y envía)
# =====================================================================
class ComponenteSeleccionAsientos:
    def __init__(self, componente_logica):
        self.componente_logica = componente_logica
        
        # Se obtiene la ruta de 'Componentes' y se sube un nivel a la raíz
        dir_componentes = os.path.dirname(os.path.abspath(__file__))
        dir_raiz = os.path.dirname(dir_componentes)
        
        # Ahora sí equivale a: ../data/seats.json
        self.ruta_seats = os.path.join(dir_raiz, "data", "seats.json")

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

    def seleccionar_asiento_vuelo(self, flight_id: str, passenger_name: str = ""):
        """Muestra los asientos del vuelo y solicita la selección por consola."""
        while True:
            # Recargar en cada intento para detectar cambios de otra terminal
            todos_los_asientos = self._cargar_asientos()
            asientos_vuelo = [s for s in todos_los_asientos if s.get("flight_id") == flight_id]

            if not asientos_vuelo:
                raise ValueError(f"No se encontraron asientos registrados para el vuelo: {flight_id}")

            fila_elegida = input("Seleccione el número de Fila: ").strip()
            columna_elegida = input("Seleccione la letra de Columna: ").strip().upper()

            asiento_valido = next(
                (s for s in asientos_vuelo if str(s.get("fila")) == fila_elegida and s.get("columna", "").upper() == columna_elegida),
                None
            )

            if not asiento_valido:
                print("[Error] El asiento ingresado no existe para este vuelo. Intente de nuevo.")
                continue

            if asiento_valido.get("ocupado"):
                print("[Error] El asiento seleccionado ya se encuentra ocupado. Intente de nuevo.")
                continue

            result = self.componente_logica.recibir_datos_seleccion(
                flight_id=flight_id,
                fila=fila_elegida,
                columna=columna_elegida,
                passenger_name=passenger_name
            )

            if result and not result.get("success"):
                print("[Aviso] Otro pasajero acaba de reservar ese asiento. Elija otro.")
                continue

            break

