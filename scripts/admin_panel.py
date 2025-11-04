"""
Panel de Administración del Sistema de Reconocimiento Facial
Interfaz completa para gestionar usuarios, ver logs y configurar el sistema
"""

import os
from face_recognition_system import FacialRecognitionSystem
from database_manager import DatabaseManager
from access_control import AccessControlSystem
from datetime import datetime

class AdminPanel:
    def __init__(self):
        """Inicializa el panel de administración"""
        self.face_system = FacialRecognitionSystem()
        self.db_manager = DatabaseManager()
        self.access_system = AccessControlSystem()
    
    def clear_screen(self):
        """Limpia la pantalla de la consola"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        """Imprime un encabezado formateado"""
        print("\n" + "=" * 70)
        print(f"{title.center(70)}")
        print("=" * 70)
    
    def main_menu(self):
        """Menú principal del panel de administración"""
        while True:
            self.clear_screen()
            self.print_header("PANEL DE ADMINISTRACIÓN - SISTEMA DE RECONOCIMIENTO FACIAL")
            
            print("\n📋 GESTIÓN DE USUARIOS")
            print("  1. Listar todos los usuarios")
            print("  2. Registrar nuevo usuario")
            print("  3. Ver detalles de usuario")
            print("  4. Eliminar usuario")
            print("  5. Actualizar nivel de acceso")
            
            print("\n🔐 CONTROL DE ACCESO")
            print("  6. Verificar acceso (tiempo real)")
            print("  7. Verificar acceso (desde imagen)")
            print("  8. Ver logs de acceso recientes")
            
            print("\n📊 REPORTES Y ESTADÍSTICAS")
            print("  9. Generar reporte de actividad")
            print("  10. Ver estadísticas del sistema")
            print("  11. Ver eventos del sistema")
            
            print("\n⚙️  CONFIGURACIÓN")
            print("  12. Configurar parámetros del sistema")
            print("  13. Backup de base de datos")
            
            print("\n  0. Salir")
            
            choice = input("\n👉 Selecciona una opción: ").strip()
            
            if choice == '1':
                self.list_users()
            elif choice == '2':
                self.register_user_menu()
            elif choice == '3':
                self.view_user_details()
            elif choice == '4':
                self.delete_user_menu()
            elif choice == '5':
                self.update_access_level()
            elif choice == '6':
                self.verify_access_realtime()
            elif choice == '7':
                self.verify_access_image()
            elif choice == '8':
                self.view_access_logs()
            elif choice == '9':
                self.generate_report()
            elif choice == '10':
                self.view_system_statistics()
            elif choice == '11':
                self.view_system_events()
            elif choice == '12':
                self.configure_system()
            elif choice == '13':
                self.backup_database()
            elif choice == '0':
                print("\n[v0] Saliendo del panel de administración...")
                break
            else:
                print("\n❌ Opción inválida")
                input("\nPresiona ENTER para continuar...")
    
    def list_users(self):
        """Lista todos los usuarios registrados"""
        self.clear_screen()
        self.print_header("USUARIOS REGISTRADOS")
        
        users = self.face_system.list_users()
        
        if not users:
            print("\n[v0] No hay usuarios registrados en el sistema")
        else:
            print(f"\nTotal de usuarios: {len(users)}")
            print("\n" + "-" * 70)
            
            for i, user in enumerate(users, 1):
                metadata = user['metadata']
                print(f"\n{i}. {user['name']}")
                print(f"   Rol: {metadata.get('role', 'N/A')}")
                print(f"   Departamento: {metadata.get('department', 'N/A')}")
                print(f"   Nivel de acceso: {metadata.get('access_level', 'N/A')}")
                print(f"   Registrado: {metadata.get('registered_at', 'N/A')}")
                
                # Obtener estadísticas de la base de datos
                stats = self.db_manager.get_user_statistics(user['name'])
                if stats:
                    print(f"   Último acceso: {stats.get('last_access', 'Nunca')}")
                    print(f"   Total de accesos: {stats.get('total_accesses', 0)}")
                
                print("-" * 70)
        
        input("\nPresiona ENTER para continuar...")
    
    def register_user_menu(self):
        """Menú para registrar nuevo usuario"""
        self.clear_screen()
        self.print_header("REGISTRAR NUEVO USUARIO")
        
        print("\nOpciones:")
        print("1. Registrar desde imagen existente")
        print("2. Registrar capturando foto con cámara")
        print("0. Volver")
        
        choice = input("\n👉 Selecciona una opción: ").strip()
        
        if choice == '1':
            self.register_from_image()
        elif choice == '2':
            self.register_from_camera()
    
    def register_from_image(self):
        """Registra usuario desde imagen"""
        print("\n" + "-" * 70)
        
        name = input("Nombre completo: ").strip()
        if not name:
            print("❌ El nombre no puede estar vacío")
            input("\nPresiona ENTER para continuar...")
            return
        
        image_path = input("Ruta de la imagen: ").strip()
        if not os.path.exists(image_path):
            print(f"❌ No se encontró la imagen en {image_path}")
            input("\nPresiona ENTER para continuar...")
            return
        
        role = input("Rol/Cargo (default: Usuario): ").strip() or "Usuario"
        department = input("Departamento (default: General): ").strip() or "General"
        access_level = input("Nivel de acceso 1-5 (default: 1): ").strip() or "1"
        
        metadata = {
            'role': role,
            'department': department,
            'access_level': access_level
        }
        
        print("\n[v0] Procesando registro...")
        success = self.face_system.register_face(name, image_path, metadata)
        
        if success:
            self.db_manager.sync_user_metadata(name, metadata)
            self.db_manager.log_system_event(
                'user_registration',
                f'Usuario registrado desde imagen: {name}',
                user_name=name,
                details=metadata
            )
            print("\n✅ Usuario registrado exitosamente")
        else:
            print("\n❌ Error al registrar usuario")
        
        input("\nPresiona ENTER para continuar...")
    
    def register_from_camera(self):
        """Registra usuario capturando foto con cámara"""
        import cv2
        
        print("\n" + "-" * 70)
        
        name = input("Nombre completo: ").strip()
        if not name:
            print("❌ El nombre no puede estar vacío")
            input("\nPresiona ENTER para continuar...")
            return
        
        role = input("Rol/Cargo (default: Usuario): ").strip() or "Usuario"
        department = input("Departamento (default: General): ").strip() or "General"
        access_level = input("Nivel de acceso 1-5 (default: 1): ").strip() or "1"
        
        metadata = {
            'role': role,
            'department': department,
            'access_level': access_level
        }
        
        print("\n[v0] Iniciando cámara...")
        print("[v0] Presiona ESPACIO para capturar | ESC para cancelar")
        
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            print("❌ No se pudo acceder a la cámara")
            input("\nPresiona ENTER para continuar...")
            return
        
        captured_image = None
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            cv2.putText(frame, "ESPACIO: Capturar | ESC: Cancelar", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Captura de Rostro', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # ESPACIO
                captured_image = frame
                break
            elif key == 27:  # ESC
                break
        
        video_capture.release()
        cv2.destroyAllWindows()
        
        if captured_image is None:
            print("❌ Captura cancelada")
            input("\nPresiona ENTER para continuar...")
            return
        
        # Guardar imagen temporal
        os.makedirs("temp_images", exist_ok=True)
        temp_path = f"temp_images/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(temp_path, captured_image)
        
        print("\n[v0] Procesando registro...")
        success = self.face_system.register_face(name, temp_path, metadata)
        
        if success:
            self.db_manager.sync_user_metadata(name, metadata)
            self.db_manager.log_system_event(
                'user_registration',
                f'Usuario registrado con cámara: {name}',
                user_name=name,
                details=metadata
            )
            print("\n✅ Usuario registrado exitosamente")
        else:
            print("\n❌ Error al registrar usuario")
        
        input("\nPresiona ENTER para continuar...")
    
    def view_user_details(self):
        """Ver detalles de un usuario específico"""
        self.clear_screen()
        self.print_header("DETALLES DE USUARIO")
        
        name = input("\nNombre del usuario: ").strip()
        
        if name not in self.face_system.known_face_names:
            print(f"\n❌ Usuario '{name}' no encontrado")
            input("\nPresiona ENTER para continuar...")
            return
        
        # Obtener estadísticas
        stats = self.db_manager.get_user_statistics(name)
        
        if stats:
            print("\n" + "-" * 70)
            print(f"USUARIO: {name}")
            print("-" * 70)
            print(f"Rol: {stats.get('role', 'N/A')}")
            print(f"Departamento: {stats.get('department', 'N/A')}")
            print(f"Nivel de acceso: {stats.get('access_level', 'N/A')}")
            print(f"Estado: {'Activo' if stats.get('active') else 'Inactivo'}")
            print(f"Registrado: {stats.get('registered_at', 'N/A')}")
            print(f"Último acceso: {stats.get('last_access', 'Nunca')}")
            print("\nESTADÍSTICAS DE ACCESO:")
            print(f"  Total de intentos: {stats.get('total_attempts', 0)}")
            print(f"  Accesos exitosos: {stats.get('successful_accesses', 0)}")
            print(f"  Accesos denegados: {stats.get('denied_accesses', 0)}")
            print(f"  Confianza promedio: {stats.get('avg_confidence', 0):.2%}")
            print("-" * 70)
            
            # Mostrar últimos accesos
            logs = self.db_manager.get_access_logs(limit=5, user_name=name)
            if logs:
                print("\nÚLTIMOS 5 ACCESOS:")
                for i, log in enumerate(logs, 1):
                    status = "✅ CONCEDIDO" if log['access_granted'] else "❌ DENEGADO"
                    print(f"  {i}. {status} - {log['timestamp']}")
                print("-" * 70)
        else:
            print(f"\n❌ No se encontraron estadísticas para {name}")
        
        input("\nPresiona ENTER para continuar...")
    
    def delete_user_menu(self):
        """Eliminar un usuario del sistema"""
        self.clear_screen()
        self.print_header("ELIMINAR USUARIO")
        
        name = input("\nNombre del usuario a eliminar: ").strip()
        
        if name not in self.face_system.known_face_names:
            print(f"\n❌ Usuario '{name}' no encontrado")
            input("\nPresiona ENTER para continuar...")
            return
        
        confirm = input(f"\n⚠️  ¿Estás seguro de eliminar a '{name}'? (s/n): ").strip().lower()
        
        if confirm == 's':
            success = self.face_system.delete_user(name)
            if success:
                self.db_manager.log_system_event(
                    'user_deletion',
                    f'Usuario eliminado: {name}',
                    user_name=name
                )
                print(f"\n✅ Usuario '{name}' eliminado exitosamente")
            else:
                print(f"\n❌ Error al eliminar usuario")
        else:
            print("\n[v0] Eliminación cancelada")
        
        input("\nPresiona ENTER para continuar...")
    
    def update_access_level(self):
        """Actualizar nivel de acceso de un usuario"""
        self.clear_screen()
        self.print_header("ACTUALIZAR NIVEL DE ACCESO")
        
        name = input("\nNombre del usuario: ").strip()
        
        if name not in self.face_system.known_face_names:
            print(f"\n❌ Usuario '{name}' no encontrado")
            input("\nPresiona ENTER para continuar...")
            return
        
        # Obtener índice del usuario
        index = self.face_system.known_face_names.index(name)
        current_metadata = self.face_system.known_face_metadata[index]
        current_level = current_metadata.get('access_level', 1)
        
        print(f"\nNivel de acceso actual: {current_level}")
        new_level = input("Nuevo nivel de acceso (1-5): ").strip()
        
        try:
            new_level = int(new_level)
            if new_level < 1 or new_level > 5:
                print("❌ El nivel debe estar entre 1 y 5")
                input("\nPresiona ENTER para continuar...")
                return
            
            # Actualizar metadata
            current_metadata['access_level'] = str(new_level)
            self.face_system.known_face_metadata[index] = current_metadata
            self.face_system.save_database()
            
            # Sincronizar con base de datos
            self.db_manager.sync_user_metadata(name, current_metadata)
            self.db_manager.log_system_event(
                'access_level_update',
                f'Nivel de acceso actualizado de {current_level} a {new_level}',
                user_name=name,
                details={'old_level': current_level, 'new_level': new_level}
            )
            
            print(f"\n✅ Nivel de acceso actualizado exitosamente")
        except ValueError:
            print("❌ Nivel inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def verify_access_realtime(self):
        """Verificar acceso en tiempo real"""
        self.clear_screen()
        self.print_header("VERIFICACIÓN DE ACCESO EN TIEMPO REAL")
        
        required_level = input("\nNivel de acceso requerido (1-5, default=1): ").strip() or "1"
        
        try:
            required_level = int(required_level)
            result = self.access_system.verify_access_realtime(required_level=required_level)
        except ValueError:
            print("❌ Nivel inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def verify_access_image(self):
        """Verificar acceso desde imagen"""
        self.clear_screen()
        self.print_header("VERIFICACIÓN DE ACCESO DESDE IMAGEN")
        
        image_path = input("\nRuta de la imagen: ").strip()
        required_level = input("Nivel de acceso requerido (1-5, default=1): ").strip() or "1"
        
        try:
            required_level = int(required_level)
            result = self.access_system.verify_access_from_image(image_path, required_level)
        except ValueError:
            print("❌ Nivel inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def view_access_logs(self):
        """Ver logs de acceso recientes"""
        self.clear_screen()
        self.print_header("LOGS DE ACCESO RECIENTES")
        
        limit = input("\nNúmero de registros a mostrar (default=20): ").strip() or "20"
        
        try:
            limit = int(limit)
            logs = self.db_manager.get_access_logs(limit=limit)
            
            if not logs:
                print("\n[v0] No hay logs registrados")
            else:
                print(f"\nMostrando últimos {len(logs)} registros:")
                print("-" * 70)
                
                for i, log in enumerate(logs, 1):
                    status = "✅ CONCEDIDO" if log['access_granted'] else "❌ DENEGADO"
                    confidence = f"{log['confidence']:.2%}" if log['confidence'] else "N/A"
                    
                    print(f"\n{i}. {status}")
                    print(f"   Usuario: {log['user_name']}")
                    print(f"   Fecha: {log['timestamp']}")
                    print(f"   Confianza: {confidence}")
                    print(f"   Método: {log['method']}")
                    print(f"   Razón: {log['reason']}")
                    print("-" * 70)
        except ValueError:
            print("❌ Número inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def generate_report(self):
        """Generar reporte de actividad"""
        self.clear_screen()
        self.print_header("GENERAR REPORTE DE ACTIVIDAD")
        
        print("\nTipos de reporte:")
        print("1. Diario (últimas 24 horas)")
        print("2. Semanal (últimos 7 días)")
        print("3. Mensual (últimos 30 días)")
        print("4. Completo")
        
        choice = input("\n👉 Selecciona tipo de reporte: ").strip()
        
        report_types = {'1': 'daily', '2': 'weekly', '3': 'monthly', '4': 'all'}
        report_type = report_types.get(choice)
        
        if not report_type:
            print("❌ Opción inválida")
            input("\nPresiona ENTER para continuar...")
            return
        
        export = input("\n¿Exportar a CSV? (s/n): ").strip().lower()
        output_file = None
        
        if export == 's':
            output_file = f"reporte_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        print("\n[v0] Generando reporte...")
        report = self.db_manager.generate_report(report_type, output_file)
        
        if report:
            self.db_manager.print_report(report)
            if output_file:
                print(f"\n✅ Reporte exportado a: {output_file}")
        else:
            print("❌ Error al generar reporte")
        
        input("\nPresiona ENTER para continuar...")
    
    def view_system_statistics(self):
        """Ver estadísticas generales del sistema"""
        self.clear_screen()
        self.print_header("ESTADÍSTICAS DEL SISTEMA")
        
        # Estadísticas de usuarios
        total_users = len(self.face_system.known_face_names)
        
        # Estadísticas de acceso
        logs = self.db_manager.get_access_logs(limit=1000)
        total_attempts = len(logs)
        granted = sum(1 for log in logs if log['access_granted'])
        denied = total_attempts - granted
        success_rate = (granted / total_attempts * 100) if total_attempts > 0 else 0
        
        print("\n" + "-" * 70)
        print("USUARIOS")
        print("-" * 70)
        print(f"Total de usuarios registrados: {total_users}")
        
        print("\n" + "-" * 70)
        print("ACCESOS (últimos 1000 registros)")
        print("-" * 70)
        print(f"Total de intentos: {total_attempts}")
        print(f"Accesos concedidos: {granted}")
        print(f"Accesos denegados: {denied}")
        print(f"Tasa de éxito: {success_rate:.2f}%")
        
        # Usuarios más activos
        user_accesses = {}
        for log in logs:
            if log['access_granted']:
                user = log['user_name']
                user_accesses[user] = user_accesses.get(user, 0) + 1
        
        if user_accesses:
            print("\n" + "-" * 70)
            print("USUARIOS MÁS ACTIVOS")
            print("-" * 70)
            sorted_users = sorted(user_accesses.items(), key=lambda x: x[1], reverse=True)
            for i, (user, count) in enumerate(sorted_users[:5], 1):
                print(f"{i}. {user}: {count} accesos")
        
        print("-" * 70)
        
        input("\nPresiona ENTER para continuar...")
    
    def view_system_events(self):
        """Ver eventos del sistema"""
        self.clear_screen()
        self.print_header("EVENTOS DEL SISTEMA")
        
        limit = input("\nNúmero de eventos a mostrar (default=20): ").strip() or "20"
        
        try:
            limit = int(limit)
            events = self.db_manager.get_system_events(limit=limit)
            
            if not events:
                print("\n[v0] No hay eventos registrados")
            else:
                print(f"\nMostrando últimos {len(events)} eventos:")
                print("-" * 70)
                
                for i, event in enumerate(events, 1):
                    print(f"\n{i}. [{event['event_type']}] {event['timestamp']}")
                    print(f"   {event['description']}")
                    if event['user_name']:
                        print(f"   Usuario: {event['user_name']}")
                    print("-" * 70)
        except ValueError:
            print("❌ Número inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def configure_system(self):
        """Configurar parámetros del sistema"""
        self.clear_screen()
        self.print_header("CONFIGURACIÓN DEL SISTEMA")
        
        print("\nParámetros actuales:")
        print(f"  Tolerancia de reconocimiento: {self.face_system.tolerance}")
        print(f"  Base de datos: {self.face_system.database_path}")
        print(f"  Base de datos SQL: {self.db_manager.db_path}")
        
        print("\n¿Qué deseas configurar?")
        print("1. Ajustar tolerancia de reconocimiento")
        print("0. Volver")
        
        choice = input("\n👉 Selecciona una opción: ").strip()
        
        if choice == '1':
            print("\nTolerancia actual:", self.face_system.tolerance)
            print("(Menor = más estricto, Mayor = más permisivo)")
            print("Rango recomendado: 0.4 - 0.7")
            
            new_tolerance = input("\nNueva tolerancia: ").strip()
            
            try:
                new_tolerance = float(new_tolerance)
                if 0.3 <= new_tolerance <= 0.8:
                    self.face_system.tolerance = new_tolerance
                    self.access_system.face_system.tolerance = new_tolerance
                    
                    self.db_manager.log_system_event(
                        'configuration_change',
                        f'Tolerancia actualizada a {new_tolerance}',
                        details={'new_tolerance': new_tolerance}
                    )
                    
                    print(f"\n✅ Tolerancia actualizada a {new_tolerance}")
                else:
                    print("❌ Valor fuera de rango recomendado")
            except ValueError:
                print("❌ Valor inválido")
        
        input("\nPresiona ENTER para continuar...")
    
    def backup_database(self):
        """Crear backup de las bases de datos"""
        self.clear_screen()
        self.print_header("BACKUP DE BASE DE DATOS")
        
        import shutil
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Crear directorio de backups
        os.makedirs("backups", exist_ok=True)
        
        try:
            # Backup de base de datos de rostros
            face_db_backup = f"backups/face_database_{timestamp}.pkl"
            shutil.copy2(self.face_system.database_path, face_db_backup)
            print(f"\n✅ Backup de rostros creado: {face_db_backup}")
            
            # Backup de base de datos SQL
            sql_db_backup = f"backups/access_control_{timestamp}.db"
            shutil.copy2(self.db_manager.db_path, sql_db_backup)
            print(f"✅ Backup de logs creado: {sql_db_backup}")
            
            self.db_manager.log_system_event(
                'backup_created',
                f'Backup creado exitosamente',
                details={'timestamp': timestamp}
            )
            
            print("\n✅ Backup completado exitosamente")
        except Exception as e:
            print(f"\n❌ Error al crear backup: {e}")
        
        input("\nPresiona ENTER para continuar...")


def main():
    """Función principal"""
    print("\n[v0] Iniciando Panel de Administración...")
    
    admin = AdminPanel()
    admin.main_menu()
    
    print("\n[v0] Panel de administración cerrado")


if __name__ == "__main__":
    main()
