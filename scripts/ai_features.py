"""
Características Avanzadas de IA para el Sistema de Control de Acceso
- Detección de emociones
- Análisis de calidad de imagen
- Detección de múltiples rostros
- Score de confianza detallado
"""

import cv2
import numpy as np
import face_recognition
from typing import List, Dict, Tuple, Optional


class AIFeatures:
    """Funcionalidades avanzadas de IA."""
    
    @staticmethod
    def detect_emotion_from_landmarks(face_landmarks: dict, face_image: np.ndarray) -> str:
        """
        Detecta emoción usando landmarks faciales reales.
        Más preciso que analizar solo pixeles.
        """
        if not face_landmarks:
            return "😐 Neutral"
        
        try:
            # Extraer puntos clave
            left_eye = np.array(face_landmarks['left_eye'])
            right_eye = np.array(face_landmarks['right_eye'])
            top_lip = np.array(face_landmarks['top_lip'])
            bottom_lip = np.array(face_landmarks['bottom_lip'])
            left_eyebrow = np.array(face_landmarks['left_eyebrow'])
            right_eyebrow = np.array(face_landmarks['right_eyebrow'])
            nose_tip = np.array(face_landmarks['nose_tip'])
            
            # ANÁLISIS 1: Apertura de la boca
            # Calcular distancia vertical entre labios
            top_lip_center = np.mean(top_lip, axis=0)
            bottom_lip_center = np.mean(bottom_lip, axis=0)
            mouth_opening = np.linalg.norm(top_lip_center - bottom_lip_center)
            
            # Calcular ancho de la boca
            mouth_width = np.linalg.norm(top_lip[0] - top_lip[6])
            
            # Ratio apertura/ancho (importante para sonrisa)
            mouth_ratio = mouth_opening / (mouth_width + 1)
            
            # ANÁLISIS 2: Curvatura de los labios (sonrisa)
            # Las esquinas de la boca suben al sonreír
            left_corner = top_lip[0]
            right_corner = top_lip[6]
            mouth_center_y = top_lip_center[1]
            
            # Si las esquinas están más arriba que el centro → sonrisa
            smile_lift_left = mouth_center_y - left_corner[1]
            smile_lift_right = mouth_center_y - right_corner[1]
            smile_indicator = (smile_lift_left + smile_lift_right) / 2
            
            # ANÁLISIS 3: Apertura de ojos
            # Calcular altura de cada ojo
            left_eye_height = np.mean([
                np.linalg.norm(left_eye[1] - left_eye[5]),
                np.linalg.norm(left_eye[2] - left_eye[4])
            ])
            right_eye_height = np.mean([
                np.linalg.norm(right_eye[1] - right_eye[5]),
                np.linalg.norm(right_eye[2] - right_eye[4])
            ])
            eye_opening = (left_eye_height + right_eye_height) / 2
            
            # ANÁLISIS 4: Posición de las cejas
            # Cejas arriba = sorpresa, cejas abajo = enojo
            left_eye_center = np.mean(left_eye, axis=0)
            right_eye_center = np.mean(right_eye, axis=0)
            left_eyebrow_center = np.mean(left_eyebrow, axis=0)
            right_eyebrow_center = np.mean(right_eyebrow, axis=0)
            
            left_eyebrow_height = left_eye_center[1] - left_eyebrow_center[1]
            right_eyebrow_height = right_eye_center[1] - right_eyebrow_center[1]
            eyebrow_height = (left_eyebrow_height + right_eyebrow_height) / 2
            
            # ANÁLISIS 5: Inclinación de cejas (enojo)
            # Cejas en V invertida = enojo
            left_eyebrow_inner = left_eyebrow[-1]
            right_eyebrow_inner = right_eyebrow[0]
            eyebrow_center_y = (left_eyebrow_inner[1] + right_eyebrow_inner[1]) / 2
            left_eyebrow_outer = left_eyebrow[0]
            right_eyebrow_outer = right_eyebrow[-1]
            eyebrow_outer_y = (left_eyebrow_outer[1] + right_eyebrow_outer[1]) / 2
            
            eyebrow_frown = eyebrow_outer_y - eyebrow_center_y
            
            # Sistema de puntuación
            scores = {
                'feliz': 0,
                'triste': 0,
                'enojado': 0,
                'sorprendido': 0,
                'neutral': 0,
                'serio': 0
            }
            
            # FELIZ/SONRIENDO - Más estricto
            if smile_indicator > 3:  # Esquinas boca hacia arriba (más estricto)
                scores['feliz'] += 50
            elif smile_indicator > 1.5:
                scores['feliz'] += 25
            
            if mouth_width > 60:  # Boca ancha (sonrisa amplia)
                scores['feliz'] += 30
            elif mouth_width > 45:
                scores['feliz'] += 15
                
            if 0.2 < mouth_ratio < 0.4:  # Boca ligeramente abierta (sonrisa)
                scores['feliz'] += 20
            
            # TRISTE - Más estricto, solo si es MUY evidente
            if smile_indicator < -2.5:  # Esquinas MUY hacia abajo
                scores['triste'] += 50
            elif smile_indicator < -1.2:
                scores['triste'] += 20
            
            if mouth_ratio < 0.08:  # Boca muy cerrada
                scores['triste'] += 25
                
            if eyebrow_height < 12:  # Cejas muy bajas
                scores['triste'] += 20
            
            # ENOJADO - Cejas fruncidas, boca tensa
            if eyebrow_frown < -4:  # Cejas muy fruncidas
                scores['enojado'] += 50
            elif eyebrow_frown < -2:
                scores['enojado'] += 25
                
            if eyebrow_height < 10:  # Cejas extremadamente bajas
                scores['enojado'] += 30
            elif eyebrow_height < 14:
                scores['enojado'] += 15
                
            if 0.08 < mouth_ratio < 0.15 and abs(smile_indicator) < 1:
                scores['enojado'] += 20
            
            # SORPRENDIDO - Muy evidente
            if eye_opening > 14:  # Ojos MUY abiertos
                scores['sorprendido'] += 50
            elif eye_opening > 11:
                scores['sorprendido'] += 20
                
            if eyebrow_height > 22:  # Cejas muy arriba
                scores['sorprendido'] += 40
            elif eyebrow_height > 18:
                scores['sorprendido'] += 20
                
            if mouth_ratio > 0.45:  # Boca muy abierta
                scores['sorprendido'] += 30
            
            # NEUTRAL - Todo en rangos normales (MÁS PUNTOS POR DEFECTO)
            if abs(smile_indicator) < 1.2:  # Boca casi recta
                scores['neutral'] += 35
                
            if 0.12 < mouth_ratio < 0.22:  # Apertura normal
                scores['neutral'] += 30
                
            if 9 < eye_opening < 11:  # Ojos normalmente abiertos
                scores['neutral'] += 30
                
            if 14 < eyebrow_height < 17:  # Cejas en posición relajada
                scores['neutral'] += 30
                
            if abs(eyebrow_frown) < 2:  # Sin fruncir cejas
                scores['neutral'] += 20
            
            # SERIO - Similar a neutral pero con más tensión
            if 0.08 < mouth_ratio < 0.15:  # Boca más cerrada
                scores['serio'] += 25
                
            if abs(smile_indicator) < 0.8:  # Boca muy recta
                scores['serio'] += 25
                
            if 10 < eye_opening < 12:  # Ojos concentrados
                scores['serio'] += 20
                
            if 13 < eyebrow_height < 16:  # Cejas ligeramente tensas
                scores['serio'] += 20
            
            # Determinar emoción
            max_emotion = max(scores, key=scores.get)
            max_score = scores[max_emotion]
            
            # Si todos los scores son bajos, defaultear a neutral
            if max_score < 40:
                max_emotion = 'neutral'
            
            # Si hay empate cerca entre neutral y serio, preferir neutral
            if abs(scores['neutral'] - scores['serio']) < 15:
                if scores['neutral'] >= scores['serio']:
                    max_emotion = 'neutral'
            
            emotion_map = {
                'feliz': '😊 Feliz/Sonriendo',
                'triste': '😔 Triste',
                'enojado': '😠 Enojado/Molesto',
                'sorprendido': '😮 Sorprendido',
                'neutral': '😐 Neutral',
                'serio': '😑 Serio/Concentrado'
            }
            
            # Agregar debug info con los scores y valores clave
            debug_info = (
                f"\n   [DEBUG] Scores: Feliz={scores['feliz']}, Triste={scores['triste']}, "
                f"Enojado={scores['enojado']}, Sorprendido={scores['sorprendido']}, "
                f"Neutral={scores['neutral']}, Serio={scores['serio']}\n"
                f"   [DEBUG] Valores: smile={smile_indicator:.1f}, mouth_ratio={mouth_ratio:.2f}, "
                f"eye_open={eye_opening:.1f}, eyebrow_h={eyebrow_height:.1f}, frown={eyebrow_frown:.1f}"
            )
            
            result = emotion_map.get(max_emotion, '😐 Neutral')
            
            # Agregar debug info para ayudar a calibrar
            return result + debug_info
            
        except Exception as e:
            return "😐 Neutral"
    
    @staticmethod
    def detect_emotion(face_encoding: np.ndarray, face_image: np.ndarray) -> str:
        """
        Detecta emoción del rostro usando análisis de características faciales.
        Analiza boca, ojos y región facial para determinar expresión.
        """
        if face_image.size == 0:
            return "😐 Neutral"
        
        # Convertir a escala de grises
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
        else:
            gray = face_image
        
        h, w = gray.shape
        
        # Dividir rostro en regiones
        third_h = h // 3
        
        # Región superior (ojos/cejas)
        eye_region = gray[0:third_h, :]
        # Región media (nariz)
        mid_region = gray[third_h:2*third_h, :]
        # Región inferior (boca)
        mouth_region = gray[2*third_h:, :]
        
        # Análisis de la región de los ojos
        eye_contrast = np.std(eye_region)
        eye_brightness = np.mean(eye_region)
        
        # Análisis de la región de la boca
        mouth_contrast = np.std(mouth_region)
        mouth_brightness = np.mean(mouth_region)
        mouth_variance = np.var(mouth_region)
        
        # Detectar bordes en región de boca (sonrisa crea más bordes)
        mouth_edges = cv2.Canny(mouth_region, 50, 150)
        edge_density = np.sum(mouth_edges > 0) / mouth_edges.size
        
        # Análisis de simetría facial
        left_half = gray[:, :w//2]
        right_half = cv2.flip(gray[:, w//2:], 1)
        
        # Redimensionar para comparar
        min_w = min(left_half.shape[1], right_half.shape[1])
        left_half = left_half[:, :min_w]
        right_half = right_half[:, :min_w]
        
        symmetry = np.mean(np.abs(left_half.astype(float) - right_half.astype(float)))
        
        # Análisis de gradientes (dirección de características)
        gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)
        gradient_intensity = np.mean(gradient_mag)
        
        # Sistema de puntuación para emociones
        scores = {
            'feliz': 0,
            'triste': 0,
            'enojado': 0,
            'sorprendido': 0,
            'neutral': 0,
            'serio': 0
        }
        
        # FELIZ/SONRIENDO
        # - Alta densidad de bordes en boca (sonrisa)
        # - Buena simetría
        # - Contraste moderado en región de boca
        if edge_density > 0.15:
            scores['feliz'] += 35
        if mouth_contrast > 25:
            scores['feliz'] += 20
        if mouth_variance > 400:
            scores['feliz'] += 15
        if symmetry < 25:
            scores['feliz'] += 15
        
        # TRISTE
        # - Baja densidad de bordes en boca
        # - Bajo contraste general
        # - Ojos con menor brillo
        if edge_density < 0.08:
            scores['triste'] += 20
        if mouth_contrast < 20:
            scores['triste'] += 25
        if eye_brightness < 100:
            scores['triste'] += 20
        if gradient_intensity < 15:
            scores['triste'] += 15
        
        # ENOJADO
        # - Alta asimetría facial (ceño fruncido)
        # - Alto contraste en región superior (cejas)
        # - Boca tensa (contraste medio-alto)
        if symmetry > 30:
            scores['enojado'] += 25
        if eye_contrast > 35:
            scores['enojado'] += 30
        if 20 < mouth_contrast < 30:
            scores['enojado'] += 20
        if gradient_intensity > 25:
            scores['enojado'] += 15
        
        # SORPRENDIDO
        # - Alto contraste en ojos (muy abiertos)
        # - Boca abierta (alta varianza)
        # - Alta intensidad de gradientes
        if eye_contrast > 40:
            scores['sorprendido'] += 30
        if mouth_variance > 600:
            scores['sorprendido'] += 25
        if gradient_intensity > 22:
            scores['sorprendido'] += 20
        if edge_density > 0.18:
            scores['sorprendido'] += 15
        
        # SERIO/CONCENTRADO
        # - Baja varianza en boca (cerrada)
        # - Contraste equilibrado
        # - Buena simetría pero sin sonrisa
        if mouth_variance < 300:
            scores['serio'] += 25
        if 15 < mouth_contrast < 25:
            scores['serio'] += 20
        if symmetry < 20:
            scores['serio'] += 15
        if 0.08 < edge_density < 0.12:
            scores['serio'] += 20
        
        # NEUTRAL
        # - Todo en rangos medios
        if 20 < mouth_contrast < 30:
            scores['neutral'] += 15
        if 300 < mouth_variance < 500:
            scores['neutral'] += 15
        if 20 < symmetry < 30:
            scores['neutral'] += 15
        if 0.10 < edge_density < 0.14:
            scores['neutral'] += 15
        
        # Determinar emoción con mayor score
        max_emotion = max(scores, key=scores.get)
        max_score = scores[max_emotion]
        
        # Si el score es muy bajo, defaultear a neutral
        if max_score < 30:
            max_emotion = 'neutral'
        
        # Mapear a emojis y texto
        emotion_map = {
            'feliz': '😊 Feliz/Sonriendo',
            'triste': '😔 Triste',
            'enojado': '😠 Enojado/Molesto',
            'sorprendido': '😮 Sorprendido',
            'neutral': '😐 Neutral',
            'serio': '😑 Serio/Concentrado'
        }
        
        return emotion_map.get(max_emotion, '😐 Neutral')
    
    @staticmethod
    def analyze_image_quality(image: np.ndarray) -> Dict[str, any]:
        """
        Analiza la calidad de la imagen para reconocimiento facial.
        Retorna un score y recomendaciones.
        """
        quality_score = 100
        issues = []
        recommendations = []
        
        # Convertir a escala de grises
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 1. Análisis de iluminación
        brightness = np.mean(gray)
        if brightness < 80:
            quality_score -= 20
            issues.append("Imagen muy oscura")
            recommendations.append("Aumentar iluminación")
        elif brightness > 200:
            quality_score -= 15
            issues.append("Imagen muy brillante")
            recommendations.append("Reducir iluminación directa")
        
        # 2. Análisis de nitidez (blur detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            quality_score -= 25
            issues.append("Imagen desenfocada")
            recommendations.append("Usar cámara estable o mejor enfoque")
        
        # 3. Análisis de contraste
        contrast = gray.std()
        if contrast < 30:
            quality_score -= 15
            issues.append("Bajo contraste")
            recommendations.append("Mejorar iluminación ambiental")
        
        # 4. Tamaño de la imagen
        if image.shape[0] < 200 or image.shape[1] < 200:
            quality_score -= 20
            issues.append("Resolución muy baja")
            recommendations.append("Usar cámara de mayor resolución")
        
        quality_level = "Excelente" if quality_score >= 85 else \
                       "Buena" if quality_score >= 70 else \
                       "Aceptable" if quality_score >= 50 else "Pobre"
        
        return {
            'score': max(0, quality_score),
            'level': quality_level,
            'brightness': brightness,
            'sharpness': laplacian_var,
            'contrast': contrast,
            'issues': issues,
            'recommendations': recommendations
        }
    
    @staticmethod
    def detect_face_landmarks(face_image: np.ndarray) -> Optional[Dict]:
        """
        Detecta puntos clave del rostro (landmarks).
        Retorna diccionario con posiciones de ojos, nariz, boca, etc.
        """
        face_landmarks_list = face_recognition.face_landmarks(face_image)
        
        if not face_landmarks_list:
            return None
        
        landmarks = face_landmarks_list[0]
        
        # Calcular características
        left_eye = np.array(landmarks['left_eye'])
        right_eye = np.array(landmarks['right_eye'])
        
        # Distancia entre ojos (útil para normalización)
        eye_distance = np.linalg.norm(left_eye.mean(axis=0) - right_eye.mean(axis=0))
        
        # Ángulo de inclinación de la cara
        eye_center_left = left_eye.mean(axis=0)
        eye_center_right = right_eye.mean(axis=0)
        
        dy = eye_center_right[1] - eye_center_left[1]
        dx = eye_center_right[0] - eye_center_left[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        return {
            'landmarks': landmarks,
            'eye_distance': eye_distance,
            'face_angle': angle,
            'is_frontal': abs(angle) < 15,  # Cara frontal si ángulo < 15°
        }
    
    @staticmethod
    def calculate_confidence_details(face_encoding: np.ndarray, 
                                    known_encodings: List[np.ndarray],
                                    tolerance: float = 0.6) -> Dict:
        """
        Calcula detalles de confianza del reconocimiento facial.
        Incluye distancias, similitudes, y análisis estadístico.
        """
        if len(known_encodings) == 0:
            return {
                'best_match_distance': None,
                'confidence_percentage': 0,
                'match_quality': 'Sin referencias',
                'all_distances': []
            }
        
        # Calcular distancias euclidianas
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        
        best_distance = float(np.min(distances))
        
        # Convertir distancia a porcentaje de confianza
        # Distancia 0 = 100% confianza, distancia 1 = 0% confianza
        confidence = max(0, (1 - best_distance) * 100)
        
        # Determinar calidad del match
        if best_distance < tolerance * 0.5:
            quality = "Excelente"
        elif best_distance < tolerance * 0.75:
            quality = "Muy Buena"
        elif best_distance < tolerance:
            quality = "Buena"
        elif best_distance < tolerance * 1.2:
            quality = "Marginal"
        else:
            quality = "Pobre"
        
        return {
            'best_match_distance': best_distance,
            'confidence_percentage': confidence,
            'match_quality': quality,
            'all_distances': distances.tolist(),
            'mean_distance': float(np.mean(distances)),
            'std_distance': float(np.std(distances)),
            'is_match': best_distance <= tolerance
        }
    
    @staticmethod
    def detect_multiple_faces(image: np.ndarray) -> List[Dict]:
        """
        Detecta múltiples rostros en una imagen.
        Retorna información detallada de cada rostro.
        """
        # Detectar ubicaciones de rostros
        face_locations = face_recognition.face_locations(image)
        
        faces_info = []
        
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # Extraer región del rostro
            face_image = image[top:bottom, left:right]
            
            # Calcular características
            width = right - left
            height = bottom - top
            area = width * height
            aspect_ratio = width / height if height > 0 else 0
            
            # Posición relativa
            img_height, img_width = image.shape[:2]
            center_x = (left + right) / 2 / img_width
            center_y = (top + bottom) / 2 / img_height
            
            # Determinar posición
            if center_x < 0.33:
                h_position = "izquierda"
            elif center_x < 0.66:
                h_position = "centro"
            else:
                h_position = "derecha"
            
            if center_y < 0.33:
                v_position = "arriba"
            elif center_y < 0.66:
                v_position = "centro"
            else:
                v_position = "abajo"
            
            faces_info.append({
                'index': i,
                'location': (top, right, bottom, left),
                'size': area,
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'position': f"{v_position}-{h_position}",
                'is_primary': i == 0  # El más grande generalmente
            })
        
        # Ordenar por tamaño (más grande primero)
        faces_info.sort(key=lambda x: x['size'], reverse=True)
        
        return faces_info
    
    @staticmethod
    def analyze_encoding_uniqueness(encoding: np.ndarray) -> Dict:
        """
        Analiza qué tan único/distintivo es un encoding facial.
        Útil para detectar si una foto es muy genérica.
        """
        # Análisis estadístico del encoding
        mean_val = float(np.mean(encoding))
        std_val = float(np.std(encoding))
        min_val = float(np.min(encoding))
        max_val = float(np.max(encoding))
        
        # Contar valores cerca de cero (menos distintivos)
        near_zero = np.sum(np.abs(encoding) < 0.1)
        zero_percentage = (near_zero / len(encoding)) * 100
        
        # Variabilidad (más variabilidad = más único)
        variability = std_val / (abs(mean_val) + 0.001)
        
        if variability > 0.5 and zero_percentage < 30:
            uniqueness = "Muy distintivo"
        elif variability > 0.3 and zero_percentage < 50:
            uniqueness = "Distintivo"
        elif variability > 0.15:
            uniqueness = "Moderado"
        else:
            uniqueness = "Poco distintivo"
        
        return {
            'uniqueness_level': uniqueness,
            'variability': variability,
            'zero_percentage': zero_percentage,
            'mean': mean_val,
            'std': std_val,
            'range': (min_val, max_val),
            'is_good_quality': variability > 0.3 and zero_percentage < 40
        }
    
    @staticmethod
    def get_ai_model_info() -> Dict:
        """
        Retorna información sobre los modelos de IA utilizados.
        """
        return {
            'face_detection_model': 'HOG (Histogram of Oriented Gradients) + CNN',
            'face_recognition_model': 'ResNet-34 (Deep Learning)',
            'encoding_dimensions': 128,
            'training_dataset': 'Millones de rostros diversos',
            'accuracy': '99.38% en LFW benchmark',
            'technology': 'Deep Metric Learning',
            'features': [
                'Detección facial con CNN',
                'Encodings de 128 dimensiones',
                'Tolerancia a rotación y escala',
                'Invariante a iluminación parcial',
                'Reconocimiento multi-rostro'
            ]
        }
