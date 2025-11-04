"""
Sistema de Control de Acceso con IA - Interfaz Gráfica Moderna
Diseño profesional con estilo moderno, animaciones y UX mejorada
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np
import face_recognition

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QPalette, QLinearGradient, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFileDialog, QSpinBox, QLineEdit, QMessageBox, QMainWindow,
    QFrame, QGridLayout, QScrollArea, QListWidget, QListWidgetItem, QProgressBar
)

# Importar módulos del proyecto
try:
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager


# ============================================================================
# ESTILOS MODERNOS
# ============================================================================

MODERN_STYLE = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
}

QTabWidget::pane {
    border: 2px solid #3a3a5c;
    border-radius: 8px;
    background: rgba(30, 30, 50, 0.95);
}

QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2d2d44, stop:1 #1a1a2e);
    color: #b8b8d4;
    padding: 12px 24px;
    margin: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #667eea, stop:1 #764ba2);
    color: white;
}

QTabBar::tab:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #4a4a6a, stop:1 #2d2d44);
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: 600;
    min-width: 120px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #5568d3, stop:1 #6439a0);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #4a5bc4, stop:1 #562f8b);
}

QPushButton:disabled {
    background: #3a3a5c;
    color: #666680;
}

QPushButton#dangerButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ff6b6b, stop:1 #ee5a6f);
}

QPushButton#dangerButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ff5252, stop:1 #e04856);
}

QPushButton#successButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #11998e, stop:1 #38ef7d);
}

QPushButton#successButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #0e8478, stop:1 #2fd66a);
}

QLabel {
    color: #e0e0f0;
    font-size: 13px;
}

QLabel#titleLabel {
    color: white;
    font-size: 24px;
    font-weight: bold;
    padding: 10px;
}

QLabel#statusLabel {
    background: rgba(20, 20, 35, 0.8);
    color: #b8b8d4;
    border-radius: 8px;
    padding: 15px;
    font-size: 14px;
    font-weight: 500;
}

QLabel#statusSuccess {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(17, 153, 142, 0.3), stop:1 rgba(56, 239, 125, 0.3));
    color: #38ef7d;
    border: 2px solid #38ef7d;
}

QLabel#statusDanger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(255, 107, 107, 0.3), stop:1 rgba(238, 90, 111, 0.3));
    color: #ff6b6b;
    border: 2px solid #ff6b6b;
}

QLabel#videoFrame {
    background: #1a1a2e;
    border: 3px solid #3a3a5c;
    border-radius: 12px;
}

QLineEdit, QSpinBox {
    background: rgba(30, 30, 50, 0.8);
    color: white;
    border: 2px solid #3a3a5c;
    border-radius: 6px;
    padding: 10px;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #667eea;
}

QListWidget {
    background: rgba(20, 20, 35, 0.8);
    color: #e0e0f0;
    border: 2px solid #3a3a5c;
    border-radius: 8px;
    padding: 5px;
    font-size: 12px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
    margin: 2px;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
}

QListWidget::item:hover {
    background: rgba(102, 126, 234, 0.3);
}

QFrame#cardFrame {
    background: rgba(30, 30, 50, 0.95);
    border: 2px solid #3a3a5c;
    border-radius: 12px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QProgressBar {
    background: rgba(30, 30, 50, 0.8);
    border: 2px solid #3a3a5c;
    border-radius: 8px;
    text-align: center;
    color: white;
    font-weight: 600;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #667eea, stop:1 #764ba2);
    border-radius: 6px;
}
"""


def cvimg_to_qpixmap(frame: np.ndarray) -> QPixmap:
    """Convierte frame BGR de OpenCV a QPixmap."""
    if frame is None or frame.size == 0:
        return QPixmap()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


# ============================================================================
# WIDGETS PERSONALIZADOS
# ============================================================================

class ModernCard(QFrame):
    """Tarjeta moderna para agrupar contenido."""
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #667eea;")
            layout.addWidget(title_label)


class StatsWidget(QWidget):
    """Widget para mostrar estadísticas."""
    def __init__(self, label: str, value: str, color: str = "#667eea", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setStyleSheet("font-size: 12px; color: #b8b8d4;")
        label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(label_label)
        
        layout.addWidget(card)


# ============================================================================
# VISTA DE ACCESO (CÁMARA)
# ============================================================================

class ModernCameraView(QWidget):
    """Vista moderna de cámara con reconocimiento facial."""
    
    def __init__(self, access_system: AccessControlSystem, parent=None):
        super().__init__(parent)
        self.access_system = access_system
        self.face_system = access_system.face_system
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.required_level = 1
        self.last_recognition = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🎥 Control de Acceso en Tiempo Real")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Panel de control
        control_card = ModernCard()
        control_layout = QHBoxLayout(control_card)
        
        control_layout.addWidget(QLabel("Nivel de acceso requerido:"))
        
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)
        self.level_spin.valueChanged.connect(self.on_level_changed)
        control_layout.addWidget(self.level_spin)
        
        control_layout.addStretch()
        
        self.start_btn = QPushButton("▶ Iniciar Cámara")
        self.start_btn.setObjectName("successButton")
        self.start_btn.clicked.connect(self.start_camera)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Detener")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_card)
        
        # Video
        video_container = QFrame()
        video_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1a1a2e, stop:1 #16213e);
                border: 3px solid #667eea;
                border-radius: 15px;
            }
        """)
        video_layout = QVBoxLayout(video_container)
        
        self.video_label = QLabel("Presiona 'Iniciar Cámara' para comenzar")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #667eea;
                font-weight: 600;
            }
        """)
        video_layout.addWidget(self.video_label)
        
        layout.addWidget(video_container, stretch=1)
        
        # Status
        self.status_label = QLabel("🟢 Sistema listo")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def on_level_changed(self, value):
        self.required_level = value
        if self.timer.isActive():
            self.status_label.setText(f"🎯 Nivel requerido: {value}")
    
    def start_camera(self):
        try:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                raise RuntimeError("No se pudo acceder a la cámara")
            
            self.timer.start(30)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"🎬 Cámara activa - Nivel requerido: {self.required_level}")
            self.last_recognition = None
        except Exception as e:
            QMessageBox.critical(self, "Error de Cámara", f"No se pudo iniciar la cámara:\n{e}")
    
    def stop_camera(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        
        self.video_label.setText("Cámara detenida")
        self.video_label.setPixmap(QPixmap())
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏸️ Cámara detenida")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyle(self.status_label.style())
    
    def update_frame(self):
        if not self.video:
            return
        
        ok, frame = self.video.read()
        if not ok or frame is None:
            return
        
        # Voltear horizontalmente para efecto espejo (más natural)
        frame = cv2.flip(frame, 1)
        
        # Reconocimiento
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        
        detected = False
        
        for (top, right, bottom, left), enc in zip(locations, encodings):
            detected = True
            name = "Desconocido"
            confidence = 0.0
            color = (255, 50, 50)  # Rojo
            thickness = 3
            
            if len(self.face_system.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(
                    self.face_system.known_face_encodings, enc, 
                    tolerance=self.face_system.tolerance
                )
                distances = face_recognition.face_distance(self.face_system.known_face_encodings, enc)
                
                if len(distances) > 0 and min(distances) < self.face_system.tolerance:
                    best_idx = int(np.argmin(distances))
                    if matches[best_idx]:
                        name = self.face_system.known_face_names[best_idx]
                        confidence = float(1 - distances[best_idx])
                        meta = self.face_system.known_face_metadata[best_idx]
                        user_level = int(meta.get('access_level', 1))
                        
                        if user_level >= self.required_level:
                            color = (50, 255, 100)  # Verde
                            thickness = 4
                            status_text = f"✅ ACCESO CONCEDIDO - {name} ({confidence:.0%})"
                            self.status_label.setText(status_text)
                            self.status_label.setObjectName("statusSuccess")
                            self.status_label.setStyle(self.status_label.style())
                            
                            # Log solo una vez por sesión
                            if self.last_recognition != name:
                                self.log_access(True, name, confidence, meta)
                                self.last_recognition = name
                        else:
                            color = (255, 165, 50)  # Naranja
                            status_text = f"⚠️ ACCESO DENEGADO - {name} (nivel insuficiente: {user_level} < {self.required_level})"
                            self.status_label.setText(status_text)
                            self.status_label.setObjectName("statusDanger")
                            self.status_label.setStyle(self.status_label.style())
                            
                            if self.last_recognition != name:
                                self.log_access(False, name, confidence, meta, "Nivel insuficiente")
                                self.last_recognition = name
            
            # Dibujar rectángulo con efecto de brillo
            cv2.rectangle(frame, (left-2, top-2), (right+2, bottom+2), (255, 255, 255), 1)
            cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
            
            # Fondo para texto
            cv2.rectangle(frame, (left, bottom - 40), (right, bottom), color, -1)
            
            # Texto
            label = name if confidence == 0 else f"{name} ({confidence:.0%})"
            cv2.putText(frame, label, (left + 6, bottom - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if not detected:
            self.status_label.setText("👤 Esperando detectar rostro...")
            self.status_label.setObjectName("statusLabel")
            self.status_label.setStyle(self.status_label.style())
            self.last_recognition = None
        
        # Mostrar frame
        pixmap = cvimg_to_qpixmap(frame)
        scaled = pixmap.scaled(self.video_label.size(), 
                              Qt.AspectRatioMode.KeepAspectRatio, 
                              Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled)
    
    def log_access(self, granted: bool, name: str, confidence: float, meta: dict, reason: str = None):
        result = {
            'timestamp': datetime.now().isoformat(),
            'access_granted': granted,
            'user': name,
            'confidence': confidence,
            'metadata': meta,
            'reason': reason or ('Acceso autorizado' if granted else 'Rostro no reconocido'),
            'method': 'realtime_gui'
        }
        try:
            self.access_system.db_manager.log_access_attempt(result)
        except Exception as e:
            print(f'[GUI] Error al registrar log: {e}')


# ============================================================================
# VISTA DE REGISTRO
# ============================================================================

class ModernRegisterView(QWidget):
    """Vista moderna para registro de usuarios."""
    
    def __init__(self, face_system: FacialRecognitionSystem, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.db = db
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview)
        self.preview_frame = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("👤 Registro de Nuevo Usuario")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Formulario
        form_card = ModernCard("Información del Usuario")
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        
        form_layout.addWidget(QLabel("Nombre completo:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Juan Pérez")
        form_layout.addWidget(self.name_edit, 0, 1)
        
        form_layout.addWidget(QLabel("Rol / Cargo:"), 1, 0)
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("Ej: Ingeniero")
        form_layout.addWidget(self.role_edit, 1, 1)
        
        form_layout.addWidget(QLabel("Departamento:"), 2, 0)
        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText("Ej: Tecnología")
        form_layout.addWidget(self.dept_edit, 2, 1)
        
        form_layout.addWidget(QLabel("Nivel de acceso:"), 3, 0)
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)
        form_layout.addWidget(self.level_spin, 3, 1)
        
        form_card.layout().addLayout(form_layout)
        layout.addWidget(form_card)
        
        # Preview de cámara
        preview_card = ModernCard("Vista Previa")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Sin vista previa")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setStyleSheet("""
            QLabel {
                background: #1a1a2e;
                border: 2px solid #3a3a5c;
                border-radius: 10px;
                font-size: 16px;
                color: #667eea;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        preview_card.layout().addLayout(preview_layout)
        layout.addWidget(preview_card, stretch=1)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.image_btn = QPushButton("📁 Desde Imagen")
        self.image_btn.clicked.connect(self.register_from_image)
        btn_layout.addWidget(self.image_btn)
        
        self.cam_btn = QPushButton("📷 Iniciar Cámara")
        self.cam_btn.setObjectName("successButton")
        self.cam_btn.clicked.connect(self.toggle_camera)
        btn_layout.addWidget(self.cam_btn)
        
        self.capture_btn = QPushButton("✅ Capturar y Registrar")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_and_register)
        btn_layout.addWidget(self.capture_btn)
        
        layout.addLayout(btn_layout)
    
    def get_metadata(self):
        return {
            'role': self.role_edit.text().strip() or 'Usuario',
            'department': self.dept_edit.text().strip() or 'General',
            'access_level': str(self.level_spin.value())
        }
    
    def validate_name(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Datos incompletos', 'Por favor ingresa el nombre del usuario.')
            return None
        return name
    
    def register_from_image(self):
        name = self.validate_name()
        if not name:
            return
        
        file, _ = QFileDialog.getOpenFileName(
            self, 'Selecciona una imagen', 
            str(Path.home()), 
            'Imágenes (*.jpg *.jpeg *.png *.bmp)'
        )
        
        if not file:
            return
        
        ok = self.face_system.register_face(name, file, self.get_metadata())
        
        if ok:
            self.db.sync_user_metadata(name, self.get_metadata())
            self.db.log_system_event('user_registration', 
                                    f'Usuario registrado desde imagen: {name}', 
                                    user_name=name, details=self.get_metadata())
            
            QMessageBox.information(self, 'Éxito', 
                                   f'✅ Usuario {name} registrado correctamente.')
            self.clear_form()
        else:
            QMessageBox.critical(self, 'Error', 
                               '❌ No se pudo registrar el usuario.\n\n'
                               'Verifica que:\n'
                               '• La imagen contenga un rostro visible\n'
                               '• El usuario no esté ya registrado')
    
    def toggle_camera(self):
        if self.timer.isActive():
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        try:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                raise RuntimeError("No se pudo acceder a la cámara")
            
            self.timer.start(30)
            self.cam_btn.setText("⏹ Detener Cámara")
            self.cam_btn.setObjectName("dangerButton")
            self.cam_btn.setStyle(self.cam_btn.style())
            self.capture_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, 'Error de Cámara', str(e))
    
    def stop_camera(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        
        self.preview_label.setText("Cámara detenida")
        self.preview_label.setPixmap(QPixmap())
        self.cam_btn.setText("📷 Iniciar Cámara")
        self.cam_btn.setObjectName("successButton")
        self.cam_btn.setStyle(self.cam_btn.style())
        self.capture_btn.setEnabled(False)
    
    def update_preview(self):
        if not self.video:
            return
        
        ok, frame = self.video.read()
        if not ok:
            return
        
        # Voltear horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)
        
        self.preview_frame = frame.copy()
        
        # Detectar rostro para feedback visual
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        
        for (top, right, bottom, left) in locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (50, 255, 100), 3)
            cv2.putText(frame, "Rostro detectado", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 100), 2)
        
        pixmap = cvimg_to_qpixmap(frame)
        scaled = pixmap.scaled(self.preview_label.size(),
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
    
    def capture_and_register(self):
        name = self.validate_name()
        if not name:
            return
        
        if self.preview_frame is None:
            QMessageBox.warning(self, 'Sin imagen', 'No hay imagen para capturar.')
            return
        
        os.makedirs('temp_images', exist_ok=True)
        path = f"temp_images/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(path, self.preview_frame)
        
        ok = self.face_system.register_face(name, path, self.get_metadata())
        
        if ok:
            self.db.sync_user_metadata(name, self.get_metadata())
            self.db.log_system_event('user_registration',
                                    f'Usuario registrado con cámara: {name}',
                                    user_name=name, details=self.get_metadata())
            
            QMessageBox.information(self, 'Éxito',
                                   f'✅ Usuario {name} registrado correctamente.')
            self.stop_camera()
            self.clear_form()
        else:
            QMessageBox.critical(self, 'Error',
                               '❌ No se pudo registrar el usuario.\n\n'
                               'Verifica que el rostro sea visible.')
    
    def clear_form(self):
        self.name_edit.clear()
        self.role_edit.clear()
        self.dept_edit.clear()
        self.level_spin.setValue(1)


# ============================================================================
# VISTA DE LOGS
# ============================================================================

class ModernLogsView(QWidget):
    """Vista moderna de logs de acceso."""
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("📊 Historial de Accesos")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_stat = StatsWidget("Total", "0", "#667eea")
        self.success_stat = StatsWidget("Exitosos", "0", "#38ef7d")
        self.denied_stat = StatsWidget("Denegados", "0", "#ff6b6b")
        
        stats_layout.addWidget(self.total_stat)
        stats_layout.addWidget(self.success_stat)
        stats_layout.addWidget(self.denied_stat)
        
        layout.addLayout(stats_layout)
        
        # Lista de logs
        logs_card = ModernCard("Registros Recientes")
        logs_layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        logs_layout.addWidget(self.list_widget)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh)
        logs_layout.addWidget(refresh_btn)
        
        logs_card.layout().addLayout(logs_layout)
        layout.addWidget(logs_card, stretch=1)
        
        self.refresh()
    
    def refresh(self):
        self.list_widget.clear()
        logs = self.db.get_access_logs(limit=100)
        
        granted = sum(1 for log in logs if log['access_granted'])
        denied = len(logs) - granted
        
        # Actualizar estadísticas
        self.update_stat(self.total_stat, str(len(logs)))
        self.update_stat(self.success_stat, str(granted))
        self.update_stat(self.denied_stat, str(denied))
        
        for log in logs:
            status = '✅' if log['access_granted'] else '❌'
            user = log.get('user_name', 'Desconocido')
            ts = log.get('timestamp', '')[:19]  # Solo fecha/hora
            method = log.get('method', 'N/A')
            confidence = log.get('confidence')
            conf_str = f" ({confidence:.0%})" if confidence else ''
            
            item_text = f"{ts}  {status}  {user}{conf_str}  [{method}]"
            item = QListWidgetItem(item_text)
            
            if log['access_granted']:
                item.setForeground(QColor("#38ef7d"))
            else:
                item.setForeground(QColor("#ff6b6b"))
            
            self.list_widget.addItem(item)
    
    def update_stat(self, widget: StatsWidget, value: str):
        # Actualizar el valor en el widget
        label = widget.findChild(QLabel)
        if label:
            for child in widget.findChildren(QLabel):
                if "font-size: 32px" in child.styleSheet():
                    child.setText(value)
                    break


# ============================================================================
# VISTA DE CONFIGURACIÓN
# ============================================================================

class ModernSettingsView(QWidget):
    """Vista moderna de configuración."""
    
    def __init__(self, face_system: FacialRecognitionSystem, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("⚙️ Configuración del Sistema")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Configuración de reconocimiento
        recog_card = ModernCard("Reconocimiento Facial")
        recog_layout = QGridLayout()
        recog_layout.setSpacing(15)
        
        recog_layout.addWidget(QLabel("Tolerancia de reconocimiento:"), 0, 0)
        
        tol_layout = QHBoxLayout()
        self.tol_spin = QSpinBox()
        self.tol_spin.setRange(30, 80)
        self.tol_spin.setValue(int(self.face_system.tolerance * 100))
        self.tol_spin.setSuffix(" %")
        tol_layout.addWidget(self.tol_spin)
        
        tol_help = QLabel("(menor = más estricto)")
        tol_help.setStyleSheet("color: #b8b8d4; font-size: 11px;")
        tol_layout.addWidget(tol_help)
        tol_layout.addStretch()
        
        recog_layout.addLayout(tol_layout, 0, 1)
        
        apply_btn = QPushButton("💾 Aplicar Cambios")
        apply_btn.clicked.connect(self.apply_settings)
        recog_layout.addWidget(apply_btn, 1, 0, 1, 2)
        
        recog_card.layout().addLayout(recog_layout)
        layout.addWidget(recog_card)
        
        # Información del sistema
        info_card = ModernCard("Información del Sistema")
        info_layout = QVBoxLayout()
        
        users_count = len(self.face_system.known_face_names)
        info_text = f"""
        <p style='font-size: 14px; line-height: 1.6;'>
        <b style='color: #667eea;'>Usuarios registrados:</b> {users_count}<br>
        <b style='color: #667eea;'>Base de datos:</b> {self.face_system.database_path}<br>
        <b style='color: #667eea;'>Logs:</b> {self.db.db_path}<br>
        </p>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        info_card.layout().addLayout(info_layout)
        layout.addWidget(info_card)
        
        # Acciones
        actions_card = ModernCard("Acciones")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        backup_btn = QPushButton("💾 Crear Backup")
        backup_btn.clicked.connect(self.create_backup)
        actions_layout.addWidget(backup_btn)
        
        actions_card.layout().addLayout(actions_layout)
        layout.addWidget(actions_card)
        
        layout.addStretch()
    
    def apply_settings(self):
        tol = self.tol_spin.value() / 100.0
        self.face_system.tolerance = tol
        
        self.db.log_system_event('configuration_change',
                                f'Tolerancia actualizada a {tol:.2f}',
                                details={'tolerance': tol})
        
        QMessageBox.information(self, 'Configuración',
                               f'✅ Tolerancia actualizada a {tol:.2f}')
    
    def create_backup(self):
        import shutil
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('backups', exist_ok=True)
        
        try:
            shutil.copy2(self.face_system.database_path, f'backups/face_database_{ts}.pkl')
            shutil.copy2(self.db.db_path, f'backups/access_control_{ts}.db')
            
            self.db.log_system_event('backup_created',
                                    'Backup creado exitosamente',
                                    details={'timestamp': ts})
            
            QMessageBox.information(self, 'Backup',
                                   f'✅ Backup creado exitosamente\n\nCarpeta: backups/')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'❌ Error al crear backup:\n{e}')


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class ModernMainWindow(QMainWindow):
    """Ventana principal con diseño moderno."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('🎯 Sistema de Control de Acceso con IA')
        self.resize(1200, 800)
        
        # Inicializar sistemas
        self.face_system = FacialRecognitionSystem()
        self.db = DatabaseManager()
        self.access_system = AccessControlSystem()
        
        self.init_ui()
    
    def init_ui(self):
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #667eea, stop:1 #764ba2);
                min-height: 80px;
            }
        """)
        header_layout = QHBoxLayout(header)
        
        logo_label = QLabel("🤖")
        logo_label.setStyleSheet("font-size: 48px;")
        header_layout.addWidget(logo_label)
        
        title_layout = QVBoxLayout()
        title_label = QLabel("Sistema de Control de Acceso")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        subtitle_label = QLabel("Reconocimiento Facial con Inteligencia Artificial")
        subtitle_label.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9);")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        self.camera_view = ModernCameraView(self.access_system)
        self.register_view = ModernRegisterView(self.face_system, self.db)
        self.logs_view = ModernLogsView(self.db)
        self.settings_view = ModernSettingsView(self.face_system, self.db)
        
        tabs.addTab(self.camera_view, "🎥 Acceso")
        tabs.addTab(self.register_view, "👤 Registro")
        tabs.addTab(self.logs_view, "📊 Historial")
        tabs.addTab(self.settings_view, "⚙️ Configuración")
        
        layout.addWidget(tabs)
    
    def closeEvent(self, event):
        # Detener cámaras al cerrar
        if hasattr(self.camera_view, 'video') and self.camera_view.video:
            self.camera_view.stop_camera()
        if hasattr(self.register_view, 'video') and self.register_view.video:
            self.register_view.stop_camera()
        event.accept()


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(MODERN_STYLE)
    
    # Font por defecto
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ModernMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
