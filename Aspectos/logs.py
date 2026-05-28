import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "logs.txt")


def registrar(accion: str, detalle: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {accion} | {detalle}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(linea)
