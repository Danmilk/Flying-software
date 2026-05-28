import os
from datetime import datetime
from functools import wraps

_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "audit_logs.txt")


def audit_logging_aspect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        flight_id      = kwargs.get('flight_id')      or (args[1] if len(args) > 1 else "Desconocido")
        fila           = kwargs.get('fila')            or (args[2] if len(args) > 2 else "")
        columna        = kwargs.get('columna')         or (args[3] if len(args) > 3 else "")
        passenger_name = kwargs.get('passenger_name') or (args[4] if len(args) > 4 else "DESCONOCIDO")
        seat           = f"{fila}{columna}".strip()    or "No especificado"

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
        if result and result.get("success"):
            print(log_message)
            with open(_LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(log_message)

        return result
    return wrapper
