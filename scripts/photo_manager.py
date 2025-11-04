"""
Sistema de Gestión de Fotos para Control de Acceso
- Guarda fotos de usuarios registrados
- Guarda fotos de accesos concedidos
- Guarda fotos de accesos denegados
- Organización por fecha y categoría
"""

import cv2
import os
from datetime import datetime
from pathlib import Path
import numpy as np


class PhotoManager:
    """Gestor de fotos del sistema de control de acceso."""
    
    def __init__(self, base_path: str = "access_photos"):
        self.base_path = Path(base_path)
        self.setup_directories()
    
    def setup_directories(self):
        """Crea estructura de carpetas."""
        directories = [
            self.base_path / "usuarios_registrados",
            self.base_path / "accesos_concedidos",
            self.base_path / "accesos_denegados",
            self.base_path / "intrusos",
            self.base_path / "registros_fallidos"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_registered_user(self, frame: np.ndarray, name: str, metadata: dict = None) -> str:
        """
        Guarda foto de usuario registrado.
        
        Args:
            frame: Frame de la cámara (BGR)
            name: Nombre del usuario
            metadata: Metadatos adicionales (rol, departamento, etc)
        
        Returns:
            Ruta del archivo guardado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_{timestamp}.jpg"
        
        folder = self.base_path / "usuarios_registrados" / safe_name
        folder.mkdir(parents=True, exist_ok=True)
        
        filepath = folder / filename
        
        # Agregar metadatos como texto en la imagen
        frame_copy = frame.copy()
        if metadata:
            y_offset = 30
            for key, value in metadata.items():
                text = f"{key}: {value}"
                cv2.putText(frame_copy, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 30
        
        cv2.imwrite(str(filepath), frame_copy)
        return str(filepath)
    
    def save_access_granted(self, frame: np.ndarray, name: str, confidence: float, 
                           metadata: dict = None) -> str:
        """Guarda foto de acceso concedido."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_").replace("/", "_")
        
        # Organizar por fecha
        date_folder = datetime.now().strftime("%Y-%m-%d")
        folder = self.base_path / "accesos_concedidos" / date_folder
        folder.mkdir(parents=True, exist_ok=True)
        
        filename = f"{safe_name}_{timestamp}_conf{confidence:.0%}.jpg"
        filepath = folder / filename
        
        # Agregar información en la imagen
        frame_copy = frame.copy()
        
        # Banner verde de éxito
        cv2.rectangle(frame_copy, (0, 0), (frame_copy.shape[1], 60), (0, 255, 0), -1)
        cv2.putText(frame_copy, f"ACCESO CONCEDIDO - {name}", (10, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame_copy, f"Confianza: {confidence:.1%} | {timestamp}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        if metadata:
            y_offset = 90
            for key, value in metadata.items():
                text = f"{key}: {value}"
                cv2.putText(frame_copy, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 25
        
        cv2.imwrite(str(filepath), frame_copy)
        return str(filepath)
    
    def save_access_denied(self, frame: np.ndarray, reason: str, 
                          name: str = "Desconocido", confidence: float = 0.0) -> str:
        """Guarda foto de acceso denegado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Organizar por fecha
        date_folder = datetime.now().strftime("%Y-%m-%d")
        folder = self.base_path / "accesos_denegados" / date_folder
        folder.mkdir(parents=True, exist_ok=True)
        
        safe_name = name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_{timestamp}.jpg"
        filepath = folder / filename
        
        # Agregar información en la imagen
        frame_copy = frame.copy()
        
        # Banner rojo de denegado
        cv2.rectangle(frame_copy, (0, 0), (frame_copy.shape[1], 80), (0, 0, 255), -1)
        cv2.putText(frame_copy, f"ACCESO DENEGADO", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(frame_copy, f"Usuario: {name} | Motivo: {reason}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame_copy, f"{timestamp}", (10, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imwrite(str(filepath), frame_copy)
        return str(filepath)
    
    def save_intruder(self, frame: np.ndarray) -> str:
        """Guarda foto de intruso (persona no reconocida intentando acceso)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Organizar por fecha
        date_folder = datetime.now().strftime("%Y-%m-%d")
        folder = self.base_path / "intrusos" / date_folder
        folder.mkdir(parents=True, exist_ok=True)
        
        filename = f"intruso_{timestamp}.jpg"
        filepath = folder / filename
        
        # Marcar como intruso
        frame_copy = frame.copy()
        cv2.rectangle(frame_copy, (0, 0), (frame_copy.shape[1], 60), (0, 0, 200), -1)
        cv2.putText(frame_copy, f"INTRUSO DETECTADO - {timestamp}", (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imwrite(str(filepath), frame_copy)
        return str(filepath)
    
    def save_failed_registration(self, frame: np.ndarray, reason: str) -> str:
        """Guarda foto de registro fallido."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = self.base_path / "registros_fallidos"
        
        filename = f"failed_{timestamp}.jpg"
        filepath = folder / filename
        
        frame_copy = frame.copy()
        cv2.putText(frame_copy, f"REGISTRO FALLIDO: {reason}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame_copy, timestamp, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imwrite(str(filepath), frame_copy)
        return str(filepath)
    
    def get_statistics(self) -> dict:
        """Obtiene estadísticas de fotos guardadas."""
        stats = {}
        
        for category in ["usuarios_registrados", "accesos_concedidos", 
                        "accesos_denegados", "intrusos", "registros_fallidos"]:
            folder = self.base_path / category
            if folder.exists():
                # Contar archivos jpg recursivamente
                count = len(list(folder.rglob("*.jpg")))
                stats[category] = count
            else:
                stats[category] = 0
        
        return stats
    
    def get_today_stats(self) -> dict:
        """Estadísticas solo de hoy."""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {
            'accesos_concedidos': 0,
            'accesos_denegados': 0,
            'intrusos': 0
        }
        
        for category in stats.keys():
            folder = self.base_path / category / today
            if folder.exists():
                stats[category] = len(list(folder.glob("*.jpg")))
        
        return stats
