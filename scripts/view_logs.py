"""
Script para visualizar logs y generar reportes
"""

from database_manager import DatabaseManager
from datetime import datetime, timedelta

def view_recent_logs():
    """Muestra los logs recientes"""
    db = DatabaseManager()
    
    print("\n" + "=" * 70)
    print("LOGS RECIENTES DE ACCESO")
    print("=" * 70)
    
    logs = db.get_access_logs(limit=20)
    
    if not logs:
        print("\n[v0] No hay logs registrados")
        return
    
    for i, log in enumerate(logs, 1):
        status = "✓ CONCEDIDO" if log['access_granted'] else "✗ DENEGADO"
        confidence = f"{log['confidence']:.2%}" if log['confidence'] else "N/A"
        
        print(f"\n{i}. {status}")
        print(f"   Usuario: {log['user_name']}")
        print(f"   Fecha: {log['timestamp']}")
        print(f"   Confianza: {confidence}")
        print(f"   Método: {log['method']}")
        print(f"   Razón: {log['reason']}")
        print("-" * 70)
    
    db.close()


def view_user_logs():
    """Muestra logs de un usuario específico"""
    db = DatabaseManager()
    
    user_name = input("\nNombre del usuario: ").strip()
    
    if not user_name:
        print("[v0] Nombre de usuario requerido")
        return
    
    print("\n" + "=" * 70)
    print(f"LOGS DE ACCESO - {user_name}")
    print("=" * 70)
    
    logs = db.get_access_logs(limit=50, user_name=user_name)
    
    if not logs:
        print(f"\n[v0] No hay logs para el usuario: {user_name}")
        return
    
    for i, log in enumerate(logs, 1):
        status = "✓ CONCEDIDO" if log['access_granted'] else "✗ DENEGADO"
        confidence = f"{log['confidence']:.2%}" if log['confidence'] else "N/A"
        
        print(f"\n{i}. {status} - {log['timestamp']}")
        print(f"   Confianza: {confidence} | Método: {log['method']}")
        print(f"   Razón: {log['reason']}")
    
    print("\n" + "=" * 70)
    
    # Mostrar estadísticas del usuario
    stats = db.get_user_statistics(user_name)
    
    if stats:
        print("\nESTADÍSTICAS DEL USUARIO")
        print("-" * 70)
        print(f"Rol: {stats.get('role', 'N/A')}")
        print(f"Departamento: {stats.get('department', 'N/A')}")
        print(f"Nivel de acceso: {stats.get('access_level', 'N/A')}")
        print(f"Registrado: {stats.get('registered_at', 'N/A')}")
        print(f"Último acceso: {stats.get('last_access', 'N/A')}")
        print(f"Total de intentos: {stats.get('total_attempts', 0)}")
        print(f"Accesos exitosos: {stats.get('successful_accesses', 0)}")
        print(f"Accesos denegados: {stats.get('denied_accesses', 0)}")
        print(f"Confianza promedio: {stats.get('avg_confidence', 0):.2%}")
        print("=" * 70)
    
    db.close()


def view_system_events():
    """Muestra eventos del sistema"""
    db = DatabaseManager()
    
    print("\n" + "=" * 70)
    print("EVENTOS DEL SISTEMA")
    print("=" * 70)
    
    events = db.get_system_events(limit=30)
    
    if not events:
        print("\n[v0] No hay eventos registrados")
        return
    
    for i, event in enumerate(events, 1):
        print(f"\n{i}. [{event['event_type']}] {event['timestamp']}")
        print(f"   {event['description']}")
        if event['user_name']:
            print(f"   Usuario: {event['user_name']}")
        print("-" * 70)
    
    db.close()


def generate_report_menu():
    """Menú para generar reportes"""
    db = DatabaseManager()
    
    print("\n" + "=" * 70)
    print("GENERACIÓN DE REPORTES")
    print("=" * 70)
    print("\nTipos de reporte:")
    print("1. Reporte diario (últimas 24 horas)")
    print("2. Reporte semanal (últimos 7 días)")
    print("3. Reporte mensual (últimos 30 días)")
    print("4. Reporte completo")
    
    choice = input("\nSelecciona tipo de reporte (1-4): ").strip()
    
    report_types = {
        '1': 'daily',
        '2': 'weekly',
        '3': 'monthly',
        '4': 'all'
    }
    
    report_type = report_types.get(choice)
    
    if not report_type:
        print("[v0] Opción inválida")
        return
    
    # Preguntar si desea exportar a CSV
    export = input("\n¿Exportar a CSV? (s/n): ").strip().lower()
    output_file = None
    
    if export == 's':
        output_file = f"reporte_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Generar reporte
    print("\n[v0] Generando reporte...")
    report = db.generate_report(report_type, output_file)
    
    if report:
        db.print_report(report)
        
        if output_file:
            print(f"\n[v0] Reporte exportado a: {output_file}")
    else:
        print("[v0] Error al generar reporte")
    
    db.close()


def main():
    """Menú principal"""
    while True:
        print("\n" + "=" * 70)
        print("SISTEMA DE VISUALIZACIÓN DE LOGS Y REPORTES")
        print("=" * 70)
        print("\nOpciones:")
        print("1. Ver logs recientes")
        print("2. Ver logs de usuario específico")
        print("3. Ver eventos del sistema")
        print("4. Generar reporte")
        print("5. Salir")
        
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        if choice == '1':
            view_recent_logs()
        elif choice == '2':
            view_user_logs()
        elif choice == '3':
            view_system_events()
        elif choice == '4':
            generate_report_menu()
        elif choice == '5':
            print("\n[v0] Saliendo...")
            break
        else:
            print("[v0] Opción inválida")


if __name__ == "__main__":
    main()
