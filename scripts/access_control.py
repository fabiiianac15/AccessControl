"""
Sistema de Control de Acceso con Reconocimiento Facial
Verifica identidad y gestiona permisos de acceso
"""

import cv2
import os
from datetime import datetime
from face_recognition_system import FacialRecognitionSystem
from database_manager import DatabaseManager

class AccessControlSystem:
    def __init__(self, database_path="face_database.pkl", tolerance=0.6):
        """
        Inicializa el sistema de control de acceso
        
        Args:
            database_path: Ruta a la base de datos de rostros
            tolerance: Tolerancia para el reconocimiento
        """
        self.face_system = FacialRecognitionSystem(database_path, tolerance)
        self.access_logs = []
        self.db_manager = DatabaseManager()
        
    def verify_access_from_image(self, image_path, required_level=1):
        """
        Verifica acceso desde una imagen
        
        Args:
            image_path: Ruta a la imagen del rostro
            required_level: Nivel de acceso requerido (1-5)
            
        Returns:
            Diccionario con resultado de la verificación
        """
        print("\n" + "=" * 60)
        print("VERIFICACIÓN DE ACCESO")
        print("=" * 60)
        
        if not os.path.exists(image_path):
            return {
                'access_granted': False,
                'reason': 'Imagen no encontrada',
                'timestamp': datetime.now().isoformat()
            }
        
        # Reconocer rostro
        name, confidence, metadata = self.face_system.recognize_face(image_path)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'method': 'image',
            'image_path': image_path
        }
        
        if name is None:
            result['access_granted'] = False
            result['reason'] = 'Rostro no reconocido'
            result['user'] = 'Desconocido'
            print("\n✗ ACCESO DENEGADO")
            print("Razón: Rostro no reconocido en el sistema")
        else:
            # Verificar nivel de acceso
            user_level = int(metadata.get('access_level', 1))
            
            if user_level >= required_level:
                result['access_granted'] = True
                result['user'] = name
                result['confidence'] = confidence
                result['metadata'] = metadata
                result['reason'] = 'Acceso autorizado'
                
                print("\n✓ ACCESO CONCEDIDO")
                print(f"Usuario: {name}")
                print(f"Confianza: {confidence:.2%}")
                print(f"Rol: {metadata.get('role', 'N/A')}")
                print(f"Departamento: {metadata.get('department', 'N/A')}")
                print(f"Nivel de acceso: {user_level}")
            else:
                result['access_granted'] = False
                result['user'] = name
                result['confidence'] = confidence
                result['metadata'] = metadata
                result['reason'] = f'Nivel de acceso insuficiente (requiere {required_level}, tiene {user_level})'
                
                print("\n✗ ACCESO DENEGADO")
                print(f"Usuario: {name}")
                print(f"Razón: Nivel de acceso insuficiente")
                print(f"Requerido: {required_level} | Actual: {user_level}")
        
        print("=" * 60)
        
        # Registrar en logs
        self.access_logs.append(result)
        self.db_manager.log_access_attempt(result)
        
        return result
    
    def verify_access_realtime(self, required_level=1, camera_index=0, timeout=30):
        """
        Verifica acceso en tiempo real usando la cámara
        
        Args:
            required_level: Nivel de acceso requerido (1-5)
            camera_index: Índice de la cámara
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Diccionario con resultado de la verificación
        """
        print("\n" + "=" * 60)
        print("VERIFICACIÓN DE ACCESO EN TIEMPO REAL")
        print("=" * 60)
        print(f"Nivel de acceso requerido: {required_level}")
        print("Posicione su rostro frente a la cámara...")
        print("Presione 'q' para cancelar")
        print("=" * 60)
        
        video_capture = cv2.VideoCapture(camera_index)
        
        if not video_capture.isOpened():
            return {
                'access_granted': False,
                'reason': 'No se pudo acceder a la cámara',
                'timestamp': datetime.now().isoformat()
            }
        
        start_time = datetime.now()
        result = None
        
        while True:
            ret, frame = video_capture.read()
            
            if not ret:
                break
            
            # Convertir a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar y reconocer rostros
            import face_recognition
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Comparar con base de datos
                if len(self.face_system.known_face_encodings) == 0:
                    name = "Sin usuarios registrados"
                    color = (0, 0, 255)
                else:
                    matches = face_recognition.compare_faces(
                        self.face_system.known_face_encodings, 
                        face_encoding, 
                        tolerance=self.face_system.tolerance
                    )
                    
                    name = "Desconocido"
                    confidence = 0
                    metadata = {}
                    color = (0, 0, 255)  # Rojo
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(
                            self.face_system.known_face_encodings, 
                            face_encoding
                        )
                        best_match_index = matches.index(True)
                        
                        name = self.face_system.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        metadata = self.face_system.known_face_metadata[best_match_index]
                        
                        # Verificar nivel de acceso
                        user_level = int(metadata.get('access_level', 1))
                        
                        if user_level >= required_level:
                            color = (0, 255, 0)  # Verde - Acceso concedido
                            
                            if result is None:  # Primera detección exitosa
                                result = {
                                    'access_granted': True,
                                    'user': name,
                                    'confidence': confidence,
                                    'metadata': metadata,
                                    'reason': 'Acceso autorizado',
                                    'timestamp': datetime.now().isoformat(),
                                    'method': 'realtime'
                                }
                                
                                print(f"\n✓ ACCESO CONCEDIDO - {name}")
                        else:
                            color = (0, 165, 255)  # Naranja - Reconocido pero sin permisos
                            
                            if result is None:
                                result = {
                                    'access_granted': False,
                                    'user': name,
                                    'confidence': confidence,
                                    'metadata': metadata,
                                    'reason': f'Nivel de acceso insuficiente',
                                    'timestamp': datetime.now().isoformat(),
                                    'method': 'realtime'
                                }
                                
                                print(f"\n✗ ACCESO DENEGADO - {name} (nivel insuficiente)")
                
                # Dibujar rectángulo y etiqueta
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                
                text = name if confidence == 0 else f"{name} ({confidence:.0%})"
                cv2.putText(frame, text, (left + 6, bottom - 6), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Mostrar información en pantalla
            status_text = "Esperando rostro..."
            status_color = (255, 255, 255)
            
            if result:
                if result['access_granted']:
                    status_text = f"ACCESO CONCEDIDO - {result['user']}"
                    status_color = (0, 255, 0)
                else:
                    status_text = f"ACCESO DENEGADO - {result.get('user', 'Desconocido')}"
                    status_color = (0, 0, 255)
            
            cv2.putText(frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Mostrar tiempo restante
            elapsed = (datetime.now() - start_time).seconds
            remaining = max(0, timeout - elapsed)
            cv2.putText(frame, f"Tiempo: {remaining}s", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Control de Acceso', frame)
            
            # Verificar condiciones de salida
            if cv2.waitKey(1) & 0xFF == ord('q'):
                if result is None:
                    result = {
                        'access_granted': False,
                        'reason': 'Verificación cancelada por el usuario',
                        'timestamp': datetime.now().isoformat()
                    }
                break
            
            if result and result['access_granted']:
                # Esperar 2 segundos para que el usuario vea el mensaje
                cv2.waitKey(2000)
                break
            
            if elapsed >= timeout:
                if result is None:
                    result = {
                        'access_granted': False,
                        'reason': 'Tiempo de espera agotado',
                        'timestamp': datetime.now().isoformat()
                    }
                break
        
        video_capture.release()
        cv2.destroyAllWindows()
        
        # Registrar en logs
        if result:
            self.access_logs.append(result)
            self.db_manager.log_access_attempt(result)
        
        return result
    
    def get_access_logs(self, limit=10):
        """
        Obtiene los últimos registros de acceso
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de registros de acceso
        """
        return self.access_logs[-limit:]
    
    def print_access_summary(self):
        """Imprime un resumen de los accesos"""
        if not self.access_logs:
            print("\n[v0] No hay registros de acceso")
            return
        
        granted = sum(1 for log in self.access_logs if log.get('access_granted', False))
        denied = len(self.access_logs) - granted
        
        print("\n" + "=" * 60)
        print("RESUMEN DE ACCESOS")
        print("=" * 60)
        print(f"Total de intentos: {len(self.access_logs)}")
        print(f"Accesos concedidos: {granted}")
        print(f"Accesos denegados: {denied}")
        print("=" * 60)
        
        print("\nÚltimos 5 registros:")
        for i, log in enumerate(self.access_logs[-5:], 1):
            status = "✓ CONCEDIDO" if log.get('access_granted') else "✗ DENEGADO"
            user = log.get('user', 'Desconocido')
            timestamp = log.get('timestamp', 'N/A')
            print(f"\n{i}. {status}")
            print(f"   Usuario: {user}")
            print(f"   Fecha: {timestamp}")
            print(f"   Razón: {log.get('reason', 'N/A')}")


def main():
    """Función principal para verificación de acceso"""
    print("\n[v0] Sistema de Control de Acceso")
    print("\nOpciones:")
    print("1. Verificar acceso desde imagen")
    print("2. Verificar acceso en tiempo real (cámara)")
    print("3. Ver resumen de accesos")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    system = AccessControlSystem()
    
    if choice == "1":
        image_path = input("\nRuta de la imagen: ").strip()
        required_level = input("Nivel de acceso requerido (1-5, default=1): ").strip() or "1"
        
        result = system.verify_access_from_image(image_path, int(required_level))
        
    elif choice == "2":
        required_level = input("\nNivel de acceso requerido (1-5, default=1): ").strip() or "1"
        timeout = input("Tiempo máximo de espera en segundos (default=30): ").strip() or "30"
        
        result = system.verify_access_realtime(int(required_level), timeout=int(timeout))
        
    elif choice == "3":
        system.print_access_summary()
    else:
        print("[v0] Opción inválida")


if __name__ == "__main__":
    main()
