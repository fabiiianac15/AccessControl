"""
Script para registrar nuevos usuarios en el sistema de reconocimiento facial
"""

import sys
import os
from face_recognition_system import FacialRecognitionSystem
from database_manager import DatabaseManager

def register_user_interactive():
    """Registra un usuario de forma interactiva"""
    print("=" * 60)
    print("REGISTRO DE NUEVO USUARIO")
    print("=" * 60)
    
    # Inicializar sistema
    system = FacialRecognitionSystem()
    db_manager = DatabaseManager()
    
    # Solicitar información del usuario
    name = input("\nNombre completo del usuario: ").strip()
    
    if not name:
        print("[v0] Error: El nombre no puede estar vacío")
        return False
    
    # Solicitar ruta de la imagen
    image_path = input("Ruta de la imagen del rostro: ").strip()
    
    if not os.path.exists(image_path):
        print(f"[v0] Error: No se encontró la imagen en {image_path}")
        return False
    
    # Solicitar metadata adicional
    print("\nInformación adicional (opcional):")
    role = input("Rol/Cargo: ").strip() or "Usuario"
    department = input("Departamento: ").strip() or "General"
    access_level = input("Nivel de acceso (1-5): ").strip() or "1"
    
    metadata = {
        'role': role,
        'department': department,
        'access_level': access_level
    }
    
    # Registrar usuario
    print("\nProcesando registro...")
    success = system.register_face(name, image_path, metadata)
    
    if success:
        print("\n✓ Usuario registrado exitosamente")
        print(f"  Nombre: {name}")
        print(f"  Rol: {role}")
        print(f"  Departamento: {department}")
        print(f"  Nivel de acceso: {access_level}")
        
        db_manager.sync_user_metadata(name, metadata)
        db_manager.log_system_event(
            'user_registration',
            f'Nuevo usuario registrado: {name}',
            user_name=name,
            details=metadata
        )
        
        return True
    else:
        print("\n✗ Error al registrar usuario")
        return False


def register_user_from_camera():
    """Registra un usuario capturando foto desde la cámara"""
    import cv2
    from datetime import datetime
    
    print("=" * 60)
    print("REGISTRO CON CÁMARA")
    print("=" * 60)
    
    # Solicitar información del usuario
    name = input("\nNombre completo del usuario: ").strip()
    
    if not name:
        print("[v0] Error: El nombre no puede estar vacío")
        return False
    
    role = input("Rol/Cargo: ").strip() or "Usuario"
    department = input("Departamento: ").strip() or "General"
    access_level = input("Nivel de acceso (1-5): ").strip() or "1"
    
    metadata = {
        'role': role,
        'department': department,
        'access_level': access_level
    }
    
    # Capturar foto
    print("\n[v0] Iniciando cámara...")
    print("[v0] Presiona ESPACIO para capturar foto")
    print("[v0] Presiona ESC para cancelar")
    
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("[v0] Error: No se pudo acceder a la cámara")
        return False
    
    captured_image = None
    
    while True:
        ret, frame = video_capture.read()
        
        if not ret:
            print("[v0] Error al capturar frame")
            break
        
        # Mostrar instrucciones en el frame
        cv2.putText(frame, "ESPACIO: Capturar | ESC: Cancelar", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Captura de Rostro', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 32:  # ESPACIO
            captured_image = frame
            print("[v0] Foto capturada")
            break
        elif key == 27:  # ESC
            print("[v0] Captura cancelada")
            break
    
    video_capture.release()
    cv2.destroyAllWindows()
    
    if captured_image is None:
        return False
    
    # Guardar imagen temporal
    os.makedirs("temp_images", exist_ok=True)
    temp_path = f"temp_images/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(temp_path, captured_image)
    
    # Registrar usuario
    system = FacialRecognitionSystem()
    db_manager = DatabaseManager()
    
    success = system.register_face(name, temp_path, metadata)
    
    if success:
        print("\n✓ Usuario registrado exitosamente")
        
        db_manager.sync_user_metadata(name, metadata)
        db_manager.log_system_event(
            'user_registration',
            f'Nuevo usuario registrado con cámara: {name}',
            user_name=name,
            details=metadata
        )
        
        return True
    else:
        print("\n✗ Error al registrar usuario")
        return False


if __name__ == "__main__":
    print("\n[v0] Sistema de Registro de Usuarios")
    print("\nOpciones:")
    print("1. Registrar desde imagen existente")
    print("2. Registrar capturando foto con cámara")
    
    choice = input("\nSelecciona una opción (1-2): ").strip()
    
    if choice == "1":
        register_user_interactive()
    elif choice == "2":
        register_user_from_camera()
    else:
        print("[v0] Opción inválida")
