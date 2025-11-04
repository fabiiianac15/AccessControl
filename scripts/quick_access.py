"""
Script rápido para verificación de acceso
Uso simple para control de acceso en tiempo real
"""

from access_control import AccessControlSystem

def quick_access_check(required_level=1):
    """
    Verificación rápida de acceso
    
    Args:
        required_level: Nivel de acceso requerido (1-5)
    """
    print("\n" + "=" * 60)
    print("SISTEMA DE CONTROL DE ACCESO")
    print("=" * 60)
    
    system = AccessControlSystem()
    
    # Verificar si hay usuarios registrados
    if len(system.face_system.known_face_names) == 0:
        print("\n[v0] ERROR: No hay usuarios registrados en el sistema")
        print("[v0] Por favor, registre usuarios primero usando register_user.py")
        return
    
    print(f"\n[v0] Usuarios registrados: {len(system.face_system.known_face_names)}")
    print(f"[v0] Nivel de acceso requerido: {required_level}")
    
    # Realizar verificación en tiempo real
    result = system.verify_access_realtime(required_level=required_level, timeout=30)
    
    # Mostrar resultado final
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    
    if result['access_granted']:
        print("✓ ACCESO CONCEDIDO")
        print(f"\nBienvenido, {result['user']}!")
        print(f"Confianza: {result['confidence']:.2%}")
        print(f"Rol: {result['metadata'].get('role', 'N/A')}")
        print(f"Departamento: {result['metadata'].get('department', 'N/A')}")
    else:
        print("✗ ACCESO DENEGADO")
        print(f"\nRazón: {result['reason']}")
        if 'user' in result and result['user'] != 'Desconocido':
            print(f"Usuario identificado: {result['user']}")
    
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Permitir especificar nivel de acceso desde línea de comandos
    required_level = 1
    
    if len(sys.argv) > 1:
        try:
            required_level = int(sys.argv[1])
            if required_level < 1 or required_level > 5:
                print("[v0] Nivel de acceso debe estar entre 1 y 5")
                sys.exit(1)
        except ValueError:
            print("[v0] Nivel de acceso debe ser un número entero")
            sys.exit(1)
    
    quick_access_check(required_level)
