from colorama import Fore, Style, init

init(autoreset=True)


def exito(mensaje: str):
    print(Fore.GREEN + f"[OK] {mensaje}")


def error(mensaje: str):
    print(Fore.RED + f"[ERROR] {mensaje}")


def info(mensaje: str):
    print(Fore.CYAN + f"[INFO] {mensaje}")


def alerta(mensaje: str):
    print(Fore.YELLOW + f"[ALERTA] {mensaje}")
