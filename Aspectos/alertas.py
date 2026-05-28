from functools import wraps


def alert_aspect(
    start_message="Iniciando proceso...",
    success_message="Proceso completado correctamente",
    error_message="Ocurrió un error en el proceso"
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print("\n================================")
            print(f"ALERTA: {start_message}")
            print("================================")
            try:
                result = func(*args, **kwargs)
                print("\n================================")
                print(f"ALERTA EXITOSA: {success_message}")
                print("================================")
                return result
            except Exception as error:
                print("\n================================")
                print(f"ALERTA ERROR: {error_message}")
                print(f"DETALLE: {str(error)}")
                print("================================")
                return {"success": False, "message": str(error)}
        return wrapper
    return decorator
