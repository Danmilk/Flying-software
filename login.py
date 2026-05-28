from colorama import Fore, Style, init

init(autoreset=True)


def login():
    print(Fore.CYAN + "=" * 40)
    print(Fore.CYAN + "   SISTEMA DE RESERVA DE VUELOS")
    print(Fore.CYAN + "=" * 40)
    print()

    while True:
        name = input(Fore.YELLOW + "Ingrese su nombre para continuar: " + Style.RESET_ALL).strip().upper()
        if name:
            print()
            print(Fore.GREEN + f"Bienvenido, {name}!")
            print()
            return name
        print(Fore.RED + "El nombre no puede estar vacio. Intente de nuevo.")
