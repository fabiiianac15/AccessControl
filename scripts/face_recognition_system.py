"""
Sistema de Reconocimiento Facial con IA
Utiliza face_recognition y OpenCV para detección y reconocimiento facial
"""

import cv2
import face_recognition
import numpy as np
import pickle
import os
from datetime import datetime
from pathlib import Path

class FacialRecognitionSystem:
    def __init__(self, database_path="face_database.pkl", tolerance=0.6):
        """
        Inicializa el sistema de reconocimiento facial
        
        Args:
            database_path: Ruta al archivo de base de datos de rostros
            tolerance: Tolerancia para el reconocimiento (menor = más estricto)
        """
        self.database_path = database_path
        self.tolerance = tolerance
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_metadata = []
        
        # Crear directorio para la base de datos si no existe
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar base de datos existente
        self.load_database()
    
    def load_database(self):
        """Carga la base de datos de rostros conocidos"""
        if os.path.exists(self.database_path):
            try:
                with open(self.database_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                    self.known_face_metadata = data.get('metadata', [])
                print(f"[v0] Base de datos cargada: {len(self.known_face_names)} usuarios registrados")
            except Exception as e:
                print(f"[v0] Error al cargar base de datos: {e}")
                self.known_face_encodings = []
                self.known_face_names = []
                self.known_face_metadata = []
        else:
            print("[v0] No se encontró base de datos existente. Creando nueva...")
    
    def save_database(self):
        """Guarda la base de datos de rostros conocidos"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'metadata': self.known_face_metadata
            }
            with open(self.database_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"[v0] Base de datos guardada exitosamente")
            return True
        except Exception as e:
            print(f"[v0] Error al guardar base de datos: {e}")
            return False
    
    def encode_face(self, image_path):
        """
        Codifica un rostro desde una imagen
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            encoding del rostro o None si no se detecta
        """
        try:
            # Cargar imagen
            image = face_recognition.load_image_file(image_path)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                print("[v0] No se detectó ningún rostro en la imagen")
                return None
            
            if len(face_locations) > 1:
                print("[v0] Se detectaron múltiples rostros. Usando el primero...")
            
            # Codificar el primer rostro detectado
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            
            return None
        except Exception as e:
            print(f"[v0] Error al codificar rostro: {e}")
            return None
    
    def register_face(self, name, image_path, metadata=None):
        """
        Registra un nuevo rostro en el sistema
        
        Args:
            name: Nombre del usuario
            image_path: Ruta a la imagen del rostro
            metadata: Información adicional (rol, departamento, etc.)
            
        Returns:
            True si el registro fue exitoso
        """
        print(f"[v0] Registrando usuario: {name}")
        
        # Verificar si el usuario ya existe
        if name in self.known_face_names:
            print(f"[v0] El usuario {name} ya está registrado")
            return False
        
        # Codificar rostro
        encoding = self.encode_face(image_path)
        
        if encoding is None:
            print("[v0] No se pudo registrar el rostro")
            return False
        
        # Agregar a la base de datos
        self.known_face_encodings.append(encoding)
        self.known_face_names.append(name)
        
        # Agregar metadata
        if metadata is None:
            metadata = {}
        metadata['registered_at'] = datetime.now().isoformat()
        self.known_face_metadata.append(metadata)
        
        # Guardar base de datos
        if self.save_database():
            print(f"[v0] Usuario {name} registrado exitosamente")
            return True
        
        return False
    
    def recognize_face(self, image_path):
        """
        Reconoce un rostro en una imagen
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Tupla (nombre, confianza, metadata) o (None, None, None) si no se reconoce
        """
        if len(self.known_face_encodings) == 0:
            print("[v0] No hay usuarios registrados en el sistema")
            return None, None, None
        
        # Codificar rostro de la imagen
        encoding = self.encode_face(image_path)
        
        if encoding is None:
            return None, None, None
        
        # Comparar con rostros conocidos
        face_distances = face_recognition.face_distance(self.known_face_encodings, encoding)
        best_match_index = np.argmin(face_distances)
        
        if face_distances[best_match_index] <= self.tolerance:
            name = self.known_face_names[best_match_index]
            confidence = 1 - face_distances[best_match_index]
            metadata = self.known_face_metadata[best_match_index]
            
            print(f"[v0] Rostro reconocido: {name} (confianza: {confidence:.2%})")
            return name, confidence, metadata
        
        print("[v0] Rostro no reconocido")
        return None, None, None
    
    def recognize_face_realtime(self, camera_index=0, duration=10):
        """
        Reconocimiento facial en tiempo real usando la cámara
        
        Args:
            camera_index: Índice de la cámara (0 por defecto)
            duration: Duración en segundos (0 = indefinido)
            
        Returns:
            Tupla (nombre, confianza, metadata) del primer rostro reconocido
        """
        print("[v0] Iniciando reconocimiento en tiempo real...")
        print("[v0] Presiona 'q' para salir")
        
        video_capture = cv2.VideoCapture(camera_index)
        
        if not video_capture.isOpened():
            print("[v0] Error: No se pudo acceder a la cámara")
            return None, None, None
        
        start_time = datetime.now()
        recognized_user = None
        
        while True:
            # Capturar frame
            ret, frame = video_capture.read()
            
            if not ret:
                print("[v0] Error al capturar frame")
                break
            
            # Convertir de BGR (OpenCV) a RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Procesar cada rostro detectado
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Comparar con rostros conocidos
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
                name = "Desconocido"
                confidence = 0
                
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        if recognized_user is None:
                            recognized_user = (name, confidence, self.known_face_metadata[best_match_index])
                            print(f"[v0] ¡Acceso concedido! Usuario: {name} (confianza: {confidence:.2%})")
                
                # Dibujar rectángulo alrededor del rostro
                color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Dibujar etiqueta con nombre
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                text = f"{name} ({confidence:.0%})" if name != "Desconocido" else name
                cv2.putText(frame, text, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
            # Mostrar frame
            cv2.imshow('Sistema de Reconocimiento Facial', frame)
            
            # Verificar si se presionó 'q' o se alcanzó la duración
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if duration > 0 and (datetime.now() - start_time).seconds >= duration:
                break
        
        # Liberar recursos
        video_capture.release()
        cv2.destroyAllWindows()
        
        return recognized_user if recognized_user else (None, None, None)
    
    def delete_user(self, name):
        """
        Elimina un usuario del sistema
        
        Args:
            name: Nombre del usuario a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        if name not in self.known_face_names:
            print(f"[v0] Usuario {name} no encontrado")
            return False
        
        index = self.known_face_names.index(name)
        
        del self.known_face_encodings[index]
        del self.known_face_names[index]
        del self.known_face_metadata[index]
        
        if self.save_database():
            print(f"[v0] Usuario {name} eliminado exitosamente")
            return True
        
        return False
    
    def list_users(self):
        """Lista todos los usuarios registrados"""
        if len(self.known_face_names) == 0:
            print("[v0] No hay usuarios registrados")
            return []
        
        print(f"\n[v0] Usuarios registrados ({len(self.known_face_names)}):")
        print("-" * 60)
        
        users = []
        for i, (name, metadata) in enumerate(zip(self.known_face_names, self.known_face_metadata), 1):
            registered_at = metadata.get('registered_at', 'N/A')
            role = metadata.get('role', 'N/A')
            print(f"{i}. {name}")
            print(f"   Rol: {role}")
            print(f"   Registrado: {registered_at}")
            print("-" * 60)
            users.append({'name': name, 'metadata': metadata})
        
        return users


if __name__ == "__main__":
    # Ejemplo de uso
    print("[v0] Inicializando sistema de reconocimiento facial...")
    system = FacialRecognitionSystem()
    
    print("\nSistema listo para usar.")
    print("Importa este módulo en otros scripts para usar el sistema.")
