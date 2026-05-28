from datetime import datetime


def audit_logging_aspect(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        flight_id = kwargs.get('flight_id') or (args[1] if len(args) > 1 else "Desconocido")
        fila      = kwargs.get('fila')      or (args[2] if len(args) > 2 else "")
        columna   = kwargs.get('columna')   or (args[3] if len(args) > 3 else "")
        seat      = f"{fila}{columna}".strip() or "No especificado"

        print("\n>>> [ASPECTO INTERCEPTOR] Capturando datos para el registro de auditoría...")
        passenger_name = input("Por favor, ingrese el nombre del pasajero para el LOG: ").strip()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_message = f"""
========== AUDIT LOG ==========
Pasajero: {passenger_name}
Vuelo: {flight_id}
Asiento: {seat}

Campo Modificado: ocupado
Valor Anterior: 0
Nuevo Valor: 1

Fecha y Hora: {timestamp}

Estado: CAMBIO REGISTRADO
================================
"""
        print(log_message)

        with open("audit_logs.txt", "a") as log_file:
            log_file.write(log_message)

        return result
    return wrapper
