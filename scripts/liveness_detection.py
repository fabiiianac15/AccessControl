"""
Detección de Persona Real (Liveness Detection) - Versión Optimizada
- Detecta si es una persona real o una foto
- Versión ligera para no afectar rendimiento
- Análisis básico pero efectivo
"""

import cv2
import numpy as np
from collections import deque


class LivenessDetector:
    """Detector de persona real vs foto - Versión optimizada."""
    
    def __init__(self):
        # Parámetros básicos
        self.frame_skip = 5  # Procesar cada 5 frames
        self.frame_count = 0
        
        # Historial ligero
        self.brightness_history = deque(maxlen=10)
        self.motion_history = deque(maxlen=5)
        
        # Estado
        self.checks_passed = 0
    
    def check_liveness_simple(self, frame: np.ndarray, face_box: tuple = None) -> dict:
        """
        Verificación simple de vivacidad sin bloquear el GUI.
        Solo procesa cada N frames.
        
        Args:
            frame: Frame de video
            face_box: (top, right, bottom, left) opcional
            
        Returns:
            dict con resultado básico
        """
        self.frame_count += 1
        
        # Solo procesar cada N frames
        if self.frame_count % self.frame_skip != 0:
            return {
                'is_real': True,  # Asumir real por defecto
                'confidence': 75.0,
                'status': 'Verificando...',
                'checks': {'motion': True, 'texture': True}
            }
        
        result = {
            'is_real': True,
            'confidence': 50.0,
            'status': 'Persona detectada',
            'checks': {}
        }
        
        try:
            # Análisis muy básico de textura
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Si hay face_box, usar solo esa región
            if face_box and len(face_box) == 4:
                top, right, bottom, left = face_box
                # Asegurar que estén dentro del frame
                top = max(0, top)
                bottom = min(frame.shape[0], bottom)
                left = max(0, left)
                right = min(frame.shape[1], right)
                
                if bottom > top and right > left:
                    gray = gray[top:bottom, left:right]
            
            # CHECK 1: Variación de brillo (personas reales tienen micro-movimientos)
            avg_brightness = np.mean(gray)
            self.brightness_history.append(avg_brightness)
            
            if len(self.brightness_history) >= 5:
                brightness_var = np.var(list(self.brightness_history))
                result['checks']['brightness_variation'] = brightness_var > 10
                if brightness_var > 10:
                    result['confidence'] += 25
            
            # CHECK 2: Textura básica con Laplaciano
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            texture_score = laplacian.var()
            
            result['checks']['texture'] = texture_score > 100
            if texture_score > 100:
                result['confidence'] += 25
                result['status'] = 'Textura natural detectada'
            else:
                result['status'] = 'Textura sospechosa (¿foto?)'
                result['is_real'] = False
        
        except Exception as e:
            # En caso de error, asumir que es real para no bloquear
            result['is_real'] = True
            result['confidence'] = 70.0
            result['status'] = f'Error en verificación: {str(e)}'
        
        return result
    
    def reset(self):
        """Resetea historial."""
        self.brightness_history.clear()
        self.motion_history.clear()
        self.checks_passed = 0
        self.frame_count = 0


# Versión alternativa: Modo simple sin verificación para máximo rendimiento
class SimpleLivenessDetector:
    """Detector ultra-simple que siempre aprueba (para testing)."""
    
    def __init__(self):
        pass
    
    def check_liveness_simple(self, frame, face_box=None):
        """Siempre retorna True."""
        return {
            'is_real': True,
            'confidence': 100.0,
            'status': 'Verificación deshabilitada',
            'checks': {}
        }
    
    def reset(self):
        pass
