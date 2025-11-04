"""
Sistema de Control de Acceso con IA - Interfaz Profesional
Diseño limpio, moderno y fácil de entender
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np
import face_recognition

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFileDialog, QSpinBox, QLineEdit, QMessageBox, QMainWindow,
    QFrame, QGridLayout, QListWidget, QListWidgetItem, QTextEdit, QGroupBox,
    QScrollArea, QProgressBar
)

# Importar módulos del proyecto
try:
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager
    from ai_features import AIFeatures
    from photo_manager import PhotoManager
    from analytics import AccessAnalytics
    from liveness_detection import LivenessDetector
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager
    from ai_features import AIFeatures
    from photo_manager import PhotoManager
    from analytics import AccessAnalytics
    from liveness_detection import LivenessDetector

# Import para integrar matplotlib en PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# ============================================================================
# ESTILOS PROFESIONALES - Inspirado en Material Design
# ============================================================================

PROFESSIONAL_STYLE = """
QMainWindow {
    background: #f5f7fa;
}

QWidget {
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

QTabWidget::pane {
    border: none;
    background: white;
    border-radius: 12px;
}

QTabBar::tab {
    background: white;
    color: #64748b;
    padding: 14px 28px;
    margin: 4px 2px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
    border: 2px solid transparent;
}

QTabBar::tab:selected {
    background: #3b82f6;
    color: white;
    border: 2px solid #3b82f6;
}

QTabBar::tab:hover:!selected {
    background: #e0f2fe;
    color: #0284c7;
}

QPushButton {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    min-height: 40px;
}

QPushButton:hover {
    background: #2563eb;
}

QPushButton:pressed {
    background: #1d4ed8;
}

QPushButton:disabled {
    background: #cbd5e1;
    color: #94a3b8;
}

QPushButton#successButton {
    background: #10b981;
}

QPushButton#successButton:hover {
    background: #059669;
}

QPushButton#dangerButton {
    background: #ef4444;
}

QPushButton#dangerButton:hover {
    background: #dc2626;
}

QPushButton#secondaryButton {
    background: white;
    color: #3b82f6;
    border: 2px solid #3b82f6;
}

QPushButton#secondaryButton:hover {
    background: #eff6ff;
}

QLabel {
    color: #1e293b;
}

QLabel#headerTitle {
    color: #0f172a;
    font-size: 28px;
    font-weight: 700;
}

QLabel#sectionTitle {
    color: #1e293b;
    font-size: 20px;
    font-weight: 600;
    padding: 8px 0;
}

QLabel#helpText {
    color: #64748b;
    font-size: 13px;
    line-height: 1.6;
}

QLabel#statusSuccess {
    background: #d1fae5;
    color: #065f46;
    border-left: 4px solid #10b981;
    border-radius: 6px;
    padding: 16px;
    font-weight: 600;
}

QLabel#statusError {
    background: #fee2e2;
    color: #991b1b;
    border-left: 4px solid #ef4444;
    border-radius: 6px;
    padding: 16px;
    font-weight: 600;
}

QLabel#statusWarning {
    background: #fef3c7;
    color: #92400e;
    border-left: 4px solid #f59e0b;
    border-radius: 6px;
    padding: 16px;
    font-weight: 600;
}

QLabel#statusInfo {
    background: #dbeafe;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 16px;
    font-weight: 600;
}

QLineEdit, QSpinBox {
    background: white;
    color: #1e293b;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #3b82f6;
    background: #f8fafc;
}

QTextEdit {
    background: white;
    color: #1e293b;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
}

QListWidget {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px;
}

QListWidget::item {
    padding: 12px;
    border-radius: 6px;
    margin: 2px 0;
    border: 1px solid transparent;
}

QListWidget::item:selected {
    background: #eff6ff;
    color: #1e40af;
    border: 1px solid #3b82f6;
}

QListWidget::item:hover {
    background: #f8fafc;
}

QFrame#card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
}

QFrame#videoFrame {
    background: #0f172a;
    border: 3px solid #e2e8f0;
    border-radius: 12px;
}

QGroupBox {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 16px;
    font-weight: 600;
    font-size: 16px;
    color: #1e293b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background: white;
}

QProgressBar {
    background: #e2e8f0;
    border: none;
    border-radius: 8px;
    text-align: center;
    color: #1e293b;
    font-weight: 600;
    min-height: 24px;
}

QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 8px;
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
# WIDGET DE TARJETA INFORMATIVA
# ============================================================================

class InfoCard(QFrame):
    """Tarjeta informativa con icono y texto."""
    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Encabezado
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Descripción
        desc_label = QLabel(description)
        desc_label.setObjectName("helpText")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)


class StatCard(QFrame):
    """Tarjeta de estadística."""
    def __init__(self, value: str, label: str, color: str = "#3b82f6", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background: {color};
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 36px; font-weight: 700; color: white;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9);")
        label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.value_label)
        layout.addWidget(label_label)
    
    def update_value(self, value: str):
        self.value_label.setText(value)


# ============================================================================
# VISTA DE ACCESO (VERIFICACIÓN)
# ============================================================================

class AccessView(QWidget):
    """Vista de verificación de acceso con explicación clara."""
    
    def __init__(self, access_system: AccessControlSystem, parent=None):
        super().__init__(parent)
        self.access_system = access_system
        self.face_system = access_system.face_system
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.required_level = 1
        self.last_user = None
        
        # Optimización de rendimiento
        self.frame_count = 0
        self.process_every_n_frames = 3  # Procesar 1 de cada 3 frames
        self.last_face_locations = []
        self.last_face_encodings = []
        
        # Sistema de fotos
        self.photo_manager = PhotoManager()
        
        # Detector de vivacidad (anti-spoofing)
        self.liveness_detector = LivenessDetector()
        self.liveness_check_active = False
        self.liveness_pending_user = None
        
        self.init_ui()
    
    def init_ui(self):
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Widget central con ancho máximo
        central_widget = QWidget()
        central_widget.setMaximumWidth(1800)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explicación clara
        info = InfoCard(
            "🎥",
            "Verificación de Acceso en Tiempo Real",
            "Verifica identidad usando la cámara. Detecta rostros y compara con usuarios registrados."
        )
        layout.addWidget(info)
        
        # Controles
        control_group = QGroupBox("Configuración")
        control_layout = QHBoxLayout(control_group)
        
        control_layout.addWidget(QLabel("Nivel de acceso:"))
        
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)
        self.level_spin.valueChanged.connect(self.on_level_changed)
        self.level_spin.setSuffix(" (1=Básico, 5=Máximo)")
        self.level_spin.setMinimumWidth(200)
        control_layout.addWidget(self.level_spin)
        
        control_layout.addStretch()
        
        self.users_label = QLabel()
        self.users_label.setStyleSheet("color: #64748b; font-weight: 600;")
        self.update_users_count()
        control_layout.addWidget(self.users_label)
        
        layout.addWidget(control_group)
        
        # Video con tamaño controlado
        video_container = QFrame()
        video_container.setObjectName("videoFrame")
        video_container.setMaximumHeight(550)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel("Presiona 'Iniciar Verificación' para comenzar")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 450)
        self.video_label.setMaximumHeight(650)
        self.video_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 16px;
                font-weight: 600;
                background: #f1f5f9;
                border-radius: 8px;
            }
        """)
        self.video_label.setScaledContents(False)
        video_layout.addWidget(self.video_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(video_container)
        
        # Status
        self.status_label = QLabel("ℹ️ Esperando inicio de verificación")
        self.status_label.setObjectName("statusInfo")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumHeight(120)
        layout.addWidget(self.status_label)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.start_btn = QPushButton("▶ Iniciar Verificación")
        self.start_btn.setObjectName("successButton")
        self.start_btn.clicked.connect(self.start_camera)
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setMaximumWidth(400)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Detener")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setMaximumWidth(250)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        # Centrar el widget
        scroll_layout = QHBoxLayout()
        scroll_layout.addStretch()
        scroll_layout.addWidget(central_widget)
        scroll_layout.addStretch()
        
        container = QWidget()
        container.setLayout(scroll_layout)
        scroll.setWidget(container)
        
        main_layout.addWidget(scroll)
    
    def update_users_count(self):
        count = len(self.face_system.known_face_names)
        self.users_label.setText(f"👥 {count} usuario{'s' if count != 1 else ''} registrado{'s' if count != 1 else ''}")
    
    def on_level_changed(self, value):
        self.required_level = value
    
    def start_camera(self):
        if len(self.face_system.known_face_names) == 0:
            QMessageBox.warning(
                self, 
                "Sin usuarios registrados",
                "⚠️ No hay usuarios registrados en el sistema.\n\n"
                "Ve a la pestaña 'Registro' para agregar usuarios primero."
            )
            return
        
        try:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                raise RuntimeError("No se pudo acceder a la cámara")
            
            self.timer.start(30)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"🔍 Buscando rostros... (Nivel requerido: {self.required_level})")
            self.status_label.setObjectName("statusInfo")
            self.status_label.setStyle(self.status_label.style())
            self.last_user = None
        except Exception as e:
            QMessageBox.critical(self, "Error de Cámara", f"❌ No se pudo iniciar la cámara:\n\n{e}")
    
    def stop_camera(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        
        self.video_label.clear()
        self.video_label.setText("Verificación detenida")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("ℹ️ Verificación detenida")
        self.status_label.setObjectName("statusInfo")
        self.status_label.setStyle(self.status_label.style())
    
    def update_frame(self):
        if not self.video:
            return
        
        ok, frame = self.video.read()
        if not ok or frame is None:
            return
        
        # Voltear para efecto espejo
        frame = cv2.flip(frame, 1)
        
        # Optimización: procesar reconocimiento solo cada N frames
        self.frame_count += 1
        should_process = (self.frame_count % self.process_every_n_frames == 0)
        
        if should_process:
            # Reducir resolución para procesamiento más rápido
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            self.last_face_locations = face_recognition.face_locations(rgb)
            self.last_face_encodings = face_recognition.face_encodings(rgb, self.last_face_locations)
        
        # Usar las últimas detecciones (incluso si no procesamos este frame)
        face_detected = False
        
        for (top, right, bottom, left), enc in zip(self.last_face_locations, self.last_face_encodings):
            face_detected = True
            
            # Escalar coordenadas de vuelta al tamaño original
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
            
            name = "Desconocido"
            confidence = 0.0
            color = (239, 68, 68)  # Rojo
            thickness = 3
            
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
                        # Sin verificación de vivacidad por ahora (causa lag)
                        # liveness_result = self.liveness_detector.check_liveness(frame, (top, right, bottom, left))
                        
                        color = (16, 185, 129)  # Verde
                        thickness = 4
                        role = meta.get('role', 'Usuario')
                        dept = meta.get('department', 'General')
                        
                        status_text = f"✅ ACCESO CONCEDIDO\n\n"
                        status_text += f"Nombre: {name}\n"
                        status_text += f"Rol: {role}\n"
                        status_text += f"Departamento: {dept}\n"
                        status_text += f"Nivel de acceso: {user_level}\n"
                        status_text += f"Confianza: {confidence:.0%}"
                        
                        self.status_label.setText(status_text)
                        self.status_label.setObjectName("statusSuccess")
                        self.status_label.setStyle(self.status_label.style())
                        
                        if self.last_user != name:
                            self.log_access(True, name, confidence, meta)
                            self.last_user = name
                    else:
                        color = (245, 158, 11)  # Naranja
                        
                        status_text = f"⚠️ ACCESO DENEGADO\n\n"
                        status_text += f"Nombre: {name}\n"
                        status_text += f"Nivel de usuario: {user_level}\n"
                        status_text += f"Nivel requerido: {self.required_level}\n"
                        status_text += f"Motivo: Nivel de acceso insuficiente"
                        
                        self.status_label.setText(status_text)
                        self.status_label.setObjectName("statusWarning")
                        self.status_label.setStyle(self.status_label.style())
                        
                        if self.last_user != name:
                            self.log_access(False, name, confidence, meta, "Nivel insuficiente")
                            self.last_user = name
            else:
                # Rostro no reconocido
                if self.last_user != "unknown":
                    status_text = f"❌ ACCESO DENEGADO\n\n"
                    status_text += f"Rostro detectado pero no reconocido en el sistema.\n"
                    status_text += f"La persona debe registrarse primero."
                    
                    self.status_label.setText(status_text)
                    self.status_label.setObjectName("statusError")
                    self.status_label.setStyle(self.status_label.style())
                    self.last_user = "unknown"
                    
                    # Guardar foto del intruso
                    try:
                        self.photo_manager.save_intruder(frame)
                    except Exception as e:
                        print(f"Error al guardar foto de intruso: {e}")
            
            # Dibujar rectángulo
            cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, -1)
            
            label = name if confidence == 0 else f"{name} ({confidence:.0%})"
            cv2.putText(frame, label, (left + 6, bottom - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if not face_detected:
            if self.last_user is not None:
                self.status_label.setText(f"🔍 Buscando rostros... (Nivel requerido: {self.required_level})")
                self.status_label.setObjectName("statusInfo")
                self.status_label.setStyle(self.status_label.style())
                self.last_user = None
        
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
            'method': 'camera_gui'
        }
        try:
            self.access_system.db_manager.log_access_attempt(result)
            
            # Guardar foto del acceso
            if self.video is not None:
                ret, current_frame = self.video.read()
                if ret and current_frame is not None:
                    current_frame = cv2.flip(current_frame, 1)
                    
                    if granted:
                        self.photo_manager.save_access_granted(
                            current_frame, name, confidence, meta
                        )
                    else:
                        self.photo_manager.save_access_denied(
                            current_frame, name, confidence, reason
                        )
        except Exception as e:
            print(f'Error al registrar log: {e}')


# ============================================================================
# VISTA DE REGISTRO
# ============================================================================

class RegisterView(QWidget):
    """Vista de registro de usuarios con explicación clara."""
    
    registered = pyqtSignal()  # Señal cuando se registra un usuario
    
    def __init__(self, face_system: FacialRecognitionSystem, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.db = db
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview)
        self.preview_frame = None
        
        # Optimización de rendimiento
        self.frame_count = 0
        
        # Sistema de fotos
        self.photo_manager = PhotoManager()
        
        self.init_ui()
    
    def init_ui(self):
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Widget central con ancho máximo
        central_widget = QWidget()
        central_widget.setMaximumWidth(1600)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explicación
        info = InfoCard(
            "👤",
            "Registro de Usuarios",
            "Registra nuevos usuarios con foto clara del rostro. Solo se guardan características matemáticas."
        )
        layout.addWidget(info)
        
        # Formulario compacto
        form_group = QGroupBox("Información del Usuario")
        form_layout = QGridLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(1, 1)
        
        form_layout.addWidget(QLabel("Nombre completo:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: María García")
        self.name_edit.setMaximumWidth(600)
        form_layout.addWidget(self.name_edit, 0, 1)
        
        form_layout.addWidget(QLabel("Rol / Cargo:"), 1, 0)
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("Ej: Gerente")
        self.role_edit.setMaximumWidth(600)
        form_layout.addWidget(self.role_edit, 1, 1)
        
        form_layout.addWidget(QLabel("Departamento:"), 2, 0)
        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText("Ej: Ventas")
        self.dept_edit.setMaximumWidth(600)
        form_layout.addWidget(self.dept_edit, 2, 1)
        
        form_layout.addWidget(QLabel("Nivel de acceso:"), 3, 0)
        level_container = QWidget()
        level_layout = QHBoxLayout(level_container)
        level_layout.setContentsMargins(0, 0, 0, 0)
        
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)
        self.level_spin.setMinimumWidth(80)
        self.level_spin.setMaximumWidth(80)
        level_layout.addWidget(self.level_spin)
        
        level_help = QLabel("(1=Básico → 5=Total)")
        level_help.setObjectName("helpText")
        level_layout.addWidget(level_help)
        level_layout.addStretch()
        
        form_layout.addWidget(level_container, 3, 1)
        
        layout.addWidget(form_group)
        
        # Preview con tamaño controlado
        preview_group = QGroupBox("Vista Previa")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(10, 15, 10, 10)
        
        self.preview_label = QLabel("No hay imagen seleccionada")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setMaximumHeight(500)
        self.preview_label.setStyleSheet("""
            QLabel {
                background: #f8fafc;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 14px;
            }
        """)
        self.preview_label.setScaledContents(False)
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(preview_group)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.image_btn = QPushButton("📁 Seleccionar Imagen")
        self.image_btn.setObjectName("secondaryButton")
        self.image_btn.clicked.connect(self.register_from_image)
        self.image_btn.setMinimumHeight(45)
        self.image_btn.setMaximumWidth(300)
        btn_layout.addWidget(self.image_btn)
        
        self.cam_btn = QPushButton("📷 Usar Cámara")
        self.cam_btn.setObjectName("secondaryButton")
        self.cam_btn.clicked.connect(self.toggle_camera)
        self.cam_btn.setMinimumHeight(45)
        self.cam_btn.setMaximumWidth(250)
        btn_layout.addWidget(self.cam_btn)
        
        self.capture_btn = QPushButton("✅ Capturar y Registrar")
        self.capture_btn.setObjectName("successButton")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_and_register)
        self.capture_btn.setMinimumHeight(45)
        self.capture_btn.setMaximumWidth(300)
        btn_layout.addWidget(self.capture_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        # Centrar el widget
        scroll_layout = QHBoxLayout()
        scroll_layout.addStretch()
        scroll_layout.addWidget(central_widget)
        scroll_layout.addStretch()
        
        container = QWidget()
        container.setLayout(scroll_layout)
        scroll.setWidget(container)
        
        main_layout.addWidget(scroll)
    
    def get_metadata(self):
        return {
            'role': self.role_edit.text().strip() or 'Usuario',
            'department': self.dept_edit.text().strip() or 'General',
            'access_level': str(self.level_spin.value())
        }
    
    def validate_name(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, 
                'Datos incompletos',
                '⚠️ Por favor ingresa el nombre completo del usuario.'
            )
            return None
        
        if name in self.face_system.known_face_names:
            QMessageBox.warning(
                self,
                'Usuario existente',
                f'⚠️ El usuario "{name}" ya está registrado en el sistema.'
            )
            return None
        
        return name
    
    def register_from_image(self):
        name = self.validate_name()
        if not name:
            return
        
        file, _ = QFileDialog.getOpenFileName(
            self,
            'Selecciona una imagen del rostro',
            str(Path.home()),
            'Imágenes (*.jpg *.jpeg *.png *.bmp)'
        )
        
        if not file:
            return
        
        # Mostrar preview
        img = cv2.imread(file)
        if img is not None:
            pixmap = cvimg_to_qpixmap(img)
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        
        # Registrar
        ok = self.face_system.register_face(name, file, self.get_metadata())
        
        if ok:
            self.db.sync_user_metadata(name, self.get_metadata())
            self.db.log_system_event(
                'user_registration',
                f'Usuario registrado desde imagen: {name}',
                user_name=name,
                details=self.get_metadata()
            )
            
            # Guardar foto del usuario registrado
            try:
                if img is not None:
                    self.photo_manager.save_registered_user(
                        img, name, self.get_metadata()
                    )
            except Exception as e:
                print(f"Error al guardar foto de usuario: {e}")
            
            QMessageBox.information(
                self,
                'Registro exitoso',
                f'✅ Usuario registrado correctamente\n\n'
                f'Nombre: {name}\n'
                f'Rol: {self.get_metadata()["role"]}\n'
                f'Nivel: {self.level_spin.value()}\n\n'
                f'Ahora puedes verificar el acceso de esta persona en la pestaña "Acceso".'
            )
            
            self.clear_form()
            self.registered.emit()
        else:
            # Guardar foto de registro fallido
            try:
                if img is not None:
                    self.photo_manager.save_failed_registration(
                        img, name, "No se detectó rostro o mala calidad"
                    )
            except Exception as e:
                print(f"Error al guardar foto de registro fallido: {e}")
            
            QMessageBox.critical(
                self,
                'Error de registro',
                '❌ No se pudo registrar el usuario.\n\n'
                'Posibles causas:\n'
                '• No se detectó un rostro en la imagen\n'
                '• La imagen tiene mala calidad\n'
                '• El rostro está muy oscuro u oculto\n\n'
                'Intenta con otra imagen más clara.'
            )
    
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
            QMessageBox.critical(self, 'Error de Cámara', f'❌ {e}')
    
    def stop_camera(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        
        self.preview_label.clear()
        self.preview_label.setText("Cámara detenida")
        self.cam_btn.setText("📷 Usar Cámara")
        self.cam_btn.setObjectName("secondaryButton")
        self.cam_btn.setStyle(self.cam_btn.style())
        self.capture_btn.setEnabled(False)
    
    def update_preview(self):
        if not self.video:
            return
        
        ok, frame = self.video.read()
        if not ok:
            return
        
        frame = cv2.flip(frame, 1)
        self.preview_frame = frame.copy()
        
        # Detectar rostro
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        
        for (top, right, bottom, left) in locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (16, 185, 129), 3)
            cv2.putText(frame, "Rostro detectado", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (16, 185, 129), 2)
        
        pixmap = cvimg_to_qpixmap(frame)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    
    def capture_and_register(self):
        name = self.validate_name()
        if not name:
            return
        
        if self.preview_frame is None:
            QMessageBox.warning(self, 'Sin imagen', '⚠️ No hay imagen para capturar.')
            return
        
        os.makedirs('temp_images', exist_ok=True)
        path = f"temp_images/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(path, self.preview_frame)
        
        ok = self.face_system.register_face(name, path, self.get_metadata())
        
        if ok:
            self.db.sync_user_metadata(name, self.get_metadata())
            self.db.log_system_event(
                'user_registration',
                f'Usuario registrado con cámara: {name}',
                user_name=name,
                details=self.get_metadata()
            )
            
            # Guardar foto del usuario registrado
            try:
                self.photo_manager.save_registered_user(
                    self.preview_frame, name, self.get_metadata()
                )
            except Exception as e:
                print(f"Error al guardar foto de usuario: {e}")
            
            QMessageBox.information(
                self,
                'Registro exitoso',
                f'✅ Usuario registrado correctamente\n\n'
                f'Nombre: {name}\n'
                f'Rol: {self.get_metadata()["role"]}\n'
                f'Nivel: {self.level_spin.value()}\n\n'
                f'La foto se guardó temporalmente en:\n{path}\n\n'
                f'Ahora puedes verificar el acceso de esta persona en la pestaña "Acceso".'
            )
            
            self.stop_camera()
            self.clear_form()
            self.registered.emit()
        else:
            # Guardar foto de registro fallido
            try:
                self.photo_manager.save_failed_registration(
                    self.preview_frame, name, "No se detectó rostro"
                )
            except Exception as e:
                print(f"Error al guardar foto de registro fallido: {e}")
            
            QMessageBox.critical(
                self,
                'Error de registro',
                '❌ No se pudo registrar el usuario.\n\n'
                'Asegúrate de que el rostro esté bien iluminado y visible.'
            )
    
    def clear_form(self):
        self.name_edit.clear()
        self.role_edit.clear()
        self.dept_edit.clear()
        self.level_spin.setValue(1)


# ============================================================================
# VISTA DE HISTORIAL
# ============================================================================

class HistoryView(QWidget):
    """Vista de historial de accesos con explicación clara."""
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explicación
        info = InfoCard(
            "📊",
            "Historial de Verificaciones",
            "Aquí se muestran todos los intentos de acceso registrados por el sistema. "
            "Cada vez que alguien intenta acceder (en la pestaña 'Acceso'), se crea un registro "
            "con la fecha, hora, usuario, resultado y nivel de confianza."
        )
        layout.addWidget(info)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        self.total_card = StatCard("0", "Total de Intentos", "#3b82f6")
        self.success_card = StatCard("0", "Accesos Concedidos", "#10b981")
        self.denied_card = StatCard("0", "Accesos Denegados", "#ef4444")
        
        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.success_card)
        stats_layout.addWidget(self.denied_card)
        
        layout.addLayout(stats_layout)
        
        # Lista
        list_group = QGroupBox("Registros Recientes (últimos 100)")
        list_layout = QVBoxLayout(list_group)
        
        self.list_widget = QListWidget()
        list_layout.addWidget(self.list_widget)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setMinimumHeight(45)
        list_layout.addWidget(refresh_btn)
        
        layout.addWidget(list_group)
        
        self.refresh()
    
    def refresh(self):
        self.list_widget.clear()
        logs = self.db.get_access_logs(limit=100)
        
        granted = sum(1 for log in logs if log['access_granted'])
        denied = len(logs) - granted
        
        self.total_card.update_value(str(len(logs)))
        self.success_card.update_value(str(granted))
        self.denied_card.update_value(str(denied))
        
        if len(logs) == 0:
            item = QListWidgetItem("ℹ️ No hay registros aún. Los accesos aparecerán aquí.")
            item.setForeground(QColor("#64748b"))
            self.list_widget.addItem(item)
            return
        
        for log in logs:
            status = '✅' if log['access_granted'] else '❌'
            user = log.get('user_name', 'Desconocido')
            ts = log.get('timestamp', '')[:19].replace('T', ' ')
            confidence = log.get('confidence')
            conf_str = f" - Confianza: {confidence:.0%}" if confidence else ''
            reason = log.get('reason', '')
            
            item_text = f"{ts}  {status}  {user}{conf_str}\n    {reason}"
            item = QListWidgetItem(item_text)
            
            if log['access_granted']:
                item.setForeground(QColor("#059669"))
            else:
                item.setForeground(QColor("#dc2626"))
            
            self.list_widget.addItem(item)


# ============================================================================
# VISTA DE CONFIGURACIÓN
# ============================================================================

class SettingsView(QWidget):
    """Vista de configuración del sistema."""
    
    def __init__(self, face_system: FacialRecognitionSystem, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explicación
        info = InfoCard(
            "⚙️",
            "Configuración del Sistema",
            "Ajusta parámetros del sistema de reconocimiento facial y gestiona backups."
        )
        layout.addWidget(info)
        
        # Reconocimiento
        recog_group = QGroupBox("Parámetros de Reconocimiento")
        recog_layout = QGridLayout(recog_group)
        recog_layout.setSpacing(15)
        
        recog_layout.addWidget(QLabel("Tolerancia:"), 0, 0)
        
        tol_container = QWidget()
        tol_layout = QHBoxLayout(tol_container)
        tol_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tol_spin = QSpinBox()
        self.tol_spin.setRange(30, 80)
        self.tol_spin.setValue(int(self.face_system.tolerance * 100))
        self.tol_spin.setSuffix(" %")
        tol_layout.addWidget(self.tol_spin)
        
        tol_help = QLabel("Menor = más estricto (menos falsos positivos)")
        tol_help.setObjectName("helpText")
        tol_layout.addWidget(tol_help)
        tol_layout.addStretch()
        
        recog_layout.addWidget(tol_container, 0, 1)
        
        apply_btn = QPushButton("💾 Aplicar Cambios")
        apply_btn.clicked.connect(self.apply_settings)
        apply_btn.setMinimumHeight(45)
        recog_layout.addWidget(apply_btn, 1, 0, 1, 2)
        
        layout.addWidget(recog_group)
        
        # Info del sistema
        info_group = QGroupBox("Información del Sistema")
        info_layout = QVBoxLayout(info_group)
        
        users_count = len(self.face_system.known_face_names)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setPlainText(
            f"👥 Usuarios registrados: {users_count}\n"
            f"💾 Base de datos de rostros: {self.face_system.database_path}\n"
            f"📊 Base de datos de logs: {self.db.db_path}\n"
            f"🔧 Tolerancia actual: {self.face_system.tolerance:.2f}\n"
        )
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Acciones
        actions_group = QGroupBox("Mantenimiento")
        actions_layout = QVBoxLayout(actions_group)
        
        backup_btn = QPushButton("💾 Crear Backup de Bases de Datos")
        backup_btn.clicked.connect(self.create_backup)
        backup_btn.setMinimumHeight(45)
        actions_layout.addWidget(backup_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
    
    def apply_settings(self):
        tol = self.tol_spin.value() / 100.0
        self.face_system.tolerance = tol
        
        self.db.log_system_event(
            'configuration_change',
            f'Tolerancia actualizada a {tol:.2f}',
            details={'tolerance': tol}
        )
        
        QMessageBox.information(
            self,
            'Configuración actualizada',
            f'✅ Tolerancia actualizada a {tol:.2f}\n\n'
            f'Este cambio afecta la precisión del reconocimiento.'
        )
    
    def create_backup(self):
        import shutil
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('backups', exist_ok=True)
        
        try:
            face_backup = f'backups/face_database_{ts}.pkl'
            db_backup = f'backups/access_control_{ts}.db'
            
            shutil.copy2(self.face_system.database_path, face_backup)
            shutil.copy2(self.db.db_path, db_backup)
            
            self.db.log_system_event(
                'backup_created',
                'Backup creado exitosamente',
                details={'timestamp': ts}
            )
            
            QMessageBox.information(
                self,
                'Backup creado',
                f'✅ Backup creado exitosamente\n\n'
                f'Archivos guardados en la carpeta "backups/":\n\n'
                f'• {face_backup}\n'
                f'• {db_backup}'
            )
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'❌ Error al crear backup:\n\n{e}')


# ============================================================================
# VISTA DE ANÁLISIS DE IA
# ============================================================================

class AIAnalysisView(QWidget):
    """Vista de análisis avanzado con IA."""
    
    def __init__(self, face_system: FacialRecognitionSystem, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.ai = AIFeatures()
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_analysis)
        self.current_frame = None
        
        # Optimización: procesar análisis cada N frames
        self.frame_count = 0
        self.process_every_n_frames = 5  # Más lento porque el análisis es pesado
        self.last_analysis = None
        
        self.init_ui()
    
    def init_ui(self):
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Widget central con ancho máximo
        central_widget = QWidget()
        central_widget.setMaximumWidth(2000)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explicación
        info = InfoCard(
            "🧠",
            "Análisis con Inteligencia Artificial",
            "Utiliza redes neuronales para detectar rostros y analizar características. Modelo: ResNet-34."
        )
        layout.addWidget(info)
        
        # Video y análisis lado a lado
        content = QHBoxLayout()
        content.setSpacing(15)
        
        # Lado izquierdo: Video
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        video_group = QGroupBox("Vista de Cámara")
        video_layout = QVBoxLayout(video_group)
        video_layout.setContentsMargins(10, 15, 10, 10)
        
        self.video_label = QLabel("Presiona 'Iniciar Análisis'")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setMaximumSize(960, 720)
        self.video_label.setStyleSheet("""
            QLabel {
                background: #f8fafc;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                color: #94a3b8;
            }
        """)
        self.video_label.setScaledContents(False)
        video_layout.addWidget(self.video_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(video_group)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("▶ Iniciar")
        self.start_btn.setObjectName("successButton")
        self.start_btn.clicked.connect(self.start_analysis)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setMaximumWidth(200)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Detener")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setMaximumWidth(200)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        
        left_layout.addLayout(btn_layout)
        content.addWidget(left_panel, stretch=1)
        
        # Lado derecho: Análisis
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Información del modelo
        model_group = QGroupBox("🤖 Modelo de IA")
        model_layout = QVBoxLayout(model_group)
        
        model_info = self.ai.get_ai_model_info()
        model_text = QTextEdit()
        model_text.setReadOnly(True)
        model_text.setMaximumHeight(180)
        model_text.setPlainText(
            f"Detección: {model_info['face_detection_model']}\n"
            f"Reconocimiento: {model_info['face_recognition_model']}\n"
            f"Dimensiones: {model_info['encoding_dimensions']}\n"
            f"Precisión: {model_info['accuracy']}\n"
            f"Tecnología: {model_info['technology']}\n\n"
            f"Características:\n" + "\n".join(f"• {f}" for f in model_info['features'])
        )
        model_layout.addWidget(model_text)
        right_layout.addWidget(model_group)
        
        # Análisis en tiempo real
        analysis_group = QGroupBox("📊 Análisis en Tiempo Real")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("Inicia el análisis para ver información detallada...")
        analysis_layout.addWidget(self.analysis_text)
        
        right_layout.addWidget(analysis_group)
        content.addWidget(right_panel, stretch=1)
        
        layout.addLayout(content)
        layout.addStretch()
        
        # Centrar el widget
        scroll_layout = QHBoxLayout()
        scroll_layout.addStretch()
        scroll_layout.addWidget(central_widget)
        scroll_layout.addStretch()
        
        container = QWidget()
        container.setLayout(scroll_layout)
        scroll.setWidget(container)
        
        main_layout.addWidget(scroll)
    
    def start_analysis(self):
        try:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                raise RuntimeError("No se pudo acceder a la cámara")
            
            self.timer.start(100)  # 100ms = ~10 FPS (suficiente para análisis)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ {e}")
    
    def stop_analysis(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        
        self.video_label.clear()
        self.video_label.setText("Análisis detenido")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.analysis_text.clear()
    
    def update_analysis(self):
        if not self.video:
            return
        
        ok, frame = self.video.read()
        if not ok or frame is None:
            return
        
        frame = cv2.flip(frame, 1)
        self.current_frame = frame.copy()
        
        # Optimización: procesar análisis pesado solo cada N frames
        self.frame_count += 1
        should_process = (self.frame_count % self.process_every_n_frames == 0)
        
        if should_process:
            # Reducir resolución para análisis más rápido
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros en imagen pequeña
            small_locations = face_recognition.face_locations(rgb)
            small_encodings = face_recognition.face_encodings(rgb, small_locations)
            
            # IMPORTANTE: Detectar landmarks faciales para análisis de emociones
            face_landmarks_list = face_recognition.face_landmarks(rgb, small_locations)
            
            # Escalar coordenadas al tamaño original
            face_locations = [(top*2, right*2, bottom*2, left*2) 
                             for (top, right, bottom, left) in small_locations]
            face_encodings = small_encodings
            
            # Análisis de múltiples rostros
            faces_info = self.ai.detect_multiple_faces(rgb)
            
            analysis_text = f"🎯 ANÁLISIS DE IA EN TIEMPO REAL\n{'='*50}\n\n"
            
            # Análisis de calidad de imagen
            quality = self.ai.analyze_image_quality(rgb)
            analysis_text += f"📷 CALIDAD DE IMAGEN:\n"
            analysis_text += f"   Score: {quality['score']}/100 ({quality['level']})\n"
            analysis_text += f"   Brillo: {quality['brightness']:.1f}\n"
            analysis_text += f"   Nitidez: {quality['sharpness']:.1f}\n"
            analysis_text += f"   Contraste: {quality['contrast']:.1f}\n"
            
            if quality['issues']:
                analysis_text += f"\n   ⚠️ Problemas detectados:\n"
                for issue in quality['issues']:
                    analysis_text += f"      • {issue}\n"
            
            if quality['recommendations']:
                analysis_text += f"\n   💡 Recomendaciones:\n"
                for rec in quality['recommendations']:
                    analysis_text += f"      • {rec}\n"
            
            analysis_text += f"\n{'='*50}\n\n"
            
            # Análisis de rostros detectados
            analysis_text += f"👥 ROSTROS DETECTADOS: {len(faces_info)}\n\n"
        else:
            # Usar último análisis si existe
            if self.last_analysis is None:
                return
            analysis_text = self.last_analysis['text']
            face_locations = self.last_analysis['locations']
            face_encodings = self.last_analysis['encodings']
            face_landmarks_list = self.last_analysis.get('landmarks', [])
        
        # Dibujar rectángulos (esto es rápido, hacerlo siempre)
        for i, (location, encoding) in enumerate(zip(face_locations, face_encodings)):
            top, right, bottom, left = location
            
            # Dibujar rectángulo
            color = (59, 130, 246)  # Azul
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            # Número del rostro
            cv2.putText(frame, f"#{i+1}", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Solo hacer análisis completo cuando procesamos
            if should_process:
                # Obtener región del rostro en imagen pequeña
                small_top, small_left = top//2, left//2
                small_bottom, small_right = bottom//2, right//2
                face_img = rgb[small_top:small_bottom, small_left:small_right]
                
                analysis_text += f"ROSTRO #{i+1}:\n"
                
                # Análisis de landmarks
                landmarks_info = self.ai.detect_face_landmarks(rgb)
                
                if landmarks_info:
                    analysis_text += f"   Ángulo: {landmarks_info['face_angle']:.1f}°\n"
                    analysis_text += f"   Frontal: {'Sí' if landmarks_info['is_frontal'] else 'No'}\n"
                    analysis_text += f"   Distancia ojos: {landmarks_info['eye_distance']:.1f}px\n"
                    
                    # Dibujar landmarks (escalados al tamaño original)
                    for landmark_type, points in landmarks_info['landmarks'].items():
                        for point in points:
                            scaled_point = (point[0]*2, point[1]*2)
                            cv2.circle(frame, scaled_point, 2, (16, 185, 129), -1)
                
                # Análisis de uniqueness del encoding
                uniqueness = self.ai.analyze_encoding_uniqueness(encoding)
                analysis_text += f"   Distintividad: {uniqueness['uniqueness_level']}\n"
                analysis_text += f"   Variabilidad: {uniqueness['variability']:.3f}\n"
                analysis_text += f"   Calidad encoding: {'Buena' if uniqueness['is_good_quality'] else 'Mejorable'}\n"
                
                # Si hay usuarios registrados, calcular confianza
                if len(self.face_system.known_face_encodings) > 0:
                    confidence_details = self.ai.calculate_confidence_details(
                        encoding, 
                        self.face_system.known_face_encodings,
                        self.face_system.tolerance
                    )
                    
                    analysis_text += f"\n   🎯 COMPARACIÓN CON BD:\n"
                    analysis_text += f"   Distancia mínima: {confidence_details['best_match_distance']:.4f}\n"
                    analysis_text += f"   Confianza: {confidence_details['confidence_percentage']:.1f}%\n"
                    analysis_text += f"   Calidad match: {confidence_details['match_quality']}\n"
                    analysis_text += f"   ¿Coincide?: {'Sí' if confidence_details['is_match'] else 'No'}\n"
                    
                    # Buscar mejor coincidencia
                    if confidence_details['is_match']:
                        distances = face_recognition.face_distance(
                            self.face_system.known_face_encodings, encoding
                        )
                        best_idx = int(np.argmin(distances))
                        name = self.face_system.known_face_names[best_idx]
                        
                        analysis_text += f"   Usuario: {name}\n"
                        
                        cv2.putText(frame, name, (left, bottom + 25),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (16, 185, 129), 2)
                
                # Emoción usando landmarks (mucho más preciso)
                if i < len(face_landmarks_list):
                    landmarks = face_landmarks_list[i]
                    emotion = self.ai.detect_emotion_from_landmarks(landmarks, face_img)
                    analysis_text += f"   Estado: {emotion}\n"
                else:
                    # Fallback al método anterior si no hay landmarks
                    if face_img.size > 0:
                        emotion = self.ai.detect_emotion(encoding, face_img)
                        analysis_text += f"   Estado: {emotion}\n"
                
                analysis_text += f"\n"
        
        # Guardar análisis para frames intermedios
        if should_process:
            self.last_analysis = {
                'text': analysis_text,
                'locations': face_locations,
                'encodings': face_encodings,
                'landmarks': face_landmarks_list
            }
            
            # Guardar posición del scroll antes de actualizar
            scrollbar = self.analysis_text.verticalScrollBar()
            old_scroll_position = scrollbar.value()
            old_max = scrollbar.maximum()
            
            # Verificar si el usuario estaba al final (auto-scroll)
            at_bottom = (old_scroll_position >= old_max - 10) if old_max > 0 else True
            
            # Actualizar texto
            self.analysis_text.setPlainText(analysis_text)
            
            # Restaurar posición del scroll
            if at_bottom:
                # Si estaba al final, mantener al final
                scrollbar.setValue(scrollbar.maximum())
            else:
                # Si no, mantener la posición relativa
                new_max = scrollbar.maximum()
                if old_max > 0:
                    # Calcular posición proporcional
                    ratio = old_scroll_position / old_max
                    new_position = int(ratio * new_max)
                    scrollbar.setValue(new_position)
                else:
                    scrollbar.setValue(old_scroll_position)
        
        # Mostrar frame
        pixmap = cvimg_to_qpixmap(frame)
        scaled = pixmap.scaled(self.video_label.size(),
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled)


# ============================================================================
# VISTA DE ESTADÍSTICAS
# ============================================================================

class StatisticsView(QWidget):
    """Vista de estadísticas con gráficas de matplotlib."""
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.analytics = AccessAnalytics(db.db_path)
        self.photo_manager = PhotoManager()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Información
        info = InfoCard(
            "📊",
            "Estadísticas y Análisis",
            "Visualización de datos con gráficas profesionales y métricas del sistema."
        )
        layout.addWidget(info)
        
        # Botones de control
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        self.refresh_btn.setMinimumHeight(38)
        self.refresh_btn.setMaximumWidth(180)
        btn_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("💾 Exportar")
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.clicked.connect(self.export_charts)
        self.export_btn.setMinimumHeight(38)
        self.export_btn.setMaximumWidth(180)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(2, 2, 2, 2)
        
        # Estadísticas principales - Grid 2x3
        stats = self.analytics.get_summary_stats()
        
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Hacer que las columnas tengan el mismo ancho
        for col in range(3):
            grid_layout.setColumnStretch(col, 1)
        
        main_cards = [
            ("Total Accesos", str(stats.get('total_accesos', 0)), "#3b82f6", 0, 0),
            ("Concedidos", str(stats.get('accesos_concedidos', 0)), "#10b981", 0, 1),
            ("Denegados", str(stats.get('accesos_denegados', 0)), "#ef4444", 0, 2),
            ("Tasa Éxito", f"{stats.get('tasa_exito', 0):.1f}%", "#8b5cf6", 1, 0),
            ("Usuarios", str(stats.get('usuarios_unicos', 0)), "#f59e0b", 1, 1),
            ("Hoy", str(stats.get('accesos_hoy', 0)), "#06b6d4", 1, 2),
        ]
        
        for title, value, color, row, col in main_cards:
            card = self.create_stat_card(title, value, color)
            grid_layout.addWidget(card, row, col)
        
        scroll_layout.addWidget(grid_container)
        
        # Estadísticas de fotos - Grid 1x4
        photo_stats = self.photo_manager.get_statistics()
        photo_container = QWidget()
        photo_grid = QGridLayout(photo_container)
        photo_grid.setSpacing(10)
        photo_grid.setContentsMargins(0, 0, 0, 0)
        
        # Hacer que las columnas tengan el mismo ancho
        for col in range(4):
            photo_grid.setColumnStretch(col, 1)
        
        photo_cards = [
            ("📸 Registrados", str(photo_stats.get('usuarios_registrados', 0)), "#3b82f6", 0, 0),
            ("✅ Accesos OK", str(photo_stats.get('accesos_concedidos', 0)), "#10b981", 0, 1),
            ("❌ Denegados", str(photo_stats.get('accesos_denegados', 0)), "#ef4444", 0, 2),
            ("🚨 Intrusos", str(photo_stats.get('intrusos', 0)), "#dc2626", 0, 3),
        ]
        
        for title, value, color, row, col in photo_cards:
            card = self.create_stat_card(title, value, color)
            photo_grid.addWidget(card, row, col)
        
        scroll_layout.addWidget(photo_container)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #cbd5e1; margin: 8px 0;")
        separator.setMaximumHeight(1)
        scroll_layout.addWidget(separator)
        
        # Título de gráficos
        charts_title = QLabel("📈 Análisis Visual")
        charts_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; margin: 5px 0;")
        scroll_layout.addWidget(charts_title)
        
        # Gráficas
        self.create_charts(scroll_layout)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Crea una tarjeta de estadística compacta y limpia."""
        card = QFrame()
        card.setFixedHeight(90)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 10px;
                border-left: 5px solid {color};
            }}
            QFrame:hover {{
                background: #f8fafc;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(2)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #64748b; 
            font-size: 10px; 
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        """)
        title_label.setWordWrap(False)
        title_label.setFixedHeight(14)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {color}; 
            font-size: 26px; 
            font-weight: bold;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        value_label.setFixedHeight(32)
        
        card_layout.addWidget(title_label)
        card_layout.addSpacing(5)
        card_layout.addWidget(value_label)
        card_layout.addStretch()
        
        return card
    
    def create_charts(self, layout: QVBoxLayout):
        """Crea todas las gráficas de forma optimizada."""
        
        # Gráfica 1: Accesos por hora (ancho completo)
        try:
            fig1 = self.analytics.create_hourly_access_chart()
            canvas1 = FigureCanvas(fig1)
            canvas1.setMinimumHeight(350)
            canvas1.setMaximumHeight(450)
            
            chart1_group = QGroupBox("📊 Distribución por Hora del Día")
            chart1_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; padding-top: 10px; }")
            chart1_layout = QVBoxLayout(chart1_group)
            chart1_layout.setContentsMargins(10, 15, 10, 10)
            chart1_layout.addWidget(canvas1)
            layout.addWidget(chart1_group)
        except Exception as e:
            print(f"Error creando gráfica de horas: {e}")
        
        # Gráfica 2: Accesos diarios (ancho completo)
        try:
            fig2 = self.analytics.create_daily_access_chart()
            canvas2 = FigureCanvas(fig2)
            canvas2.setMinimumHeight(350)
            canvas2.setMaximumHeight(450)
            
            chart2_group = QGroupBox("📅 Accesos Diarios (Últimos 30 Días)")
            chart2_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; padding-top: 10px; }")
            chart2_layout = QVBoxLayout(chart2_group)
            chart2_layout.setContentsMargins(10, 15, 10, 10)
            chart2_layout.addWidget(canvas2)
            layout.addWidget(chart2_group)
        except Exception as e:
            print(f"Error creando gráfica diaria: {e}")
        
        # Row con 2 gráficas lado a lado
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)
        
        # Gráfica 3: Top usuarios
        try:
            fig3 = self.analytics.create_top_users_chart()
            canvas3 = FigureCanvas(fig3)
            canvas3.setMinimumHeight(350)
            canvas3.setMaximumHeight(450)
            
            chart3_group = QGroupBox("👥 Usuarios Más Activos")
            chart3_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; padding-top: 10px; }")
            chart3_layout = QVBoxLayout(chart3_group)
            chart3_layout.setContentsMargins(10, 15, 10, 10)
            chart3_layout.addWidget(canvas3)
            row_layout.addWidget(chart3_group)
        except Exception as e:
            print(f"Error creando gráfica de usuarios: {e}")
        
        # Gráfica 4: Distribución de confianza
        try:
            fig4 = self.analytics.create_confidence_distribution()
            canvas4 = FigureCanvas(fig4)
            canvas4.setMinimumHeight(350)
            canvas4.setMaximumHeight(450)
            
            chart4_group = QGroupBox("📈 Niveles de Confianza")
            chart4_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; padding-top: 10px; }")
            chart4_layout = QVBoxLayout(chart4_group)
            chart4_layout.setContentsMargins(10, 15, 10, 10)
            chart4_layout.addWidget(canvas4)
            row_layout.addWidget(chart4_group)
        except Exception as e:
            print(f"Error creando gráfica de confianza: {e}")
        
        layout.addLayout(row_layout)
        
        # Gráfica 5: Razones de denegación (ancho completo, más pequeña)
        try:
            fig5 = self.analytics.create_denial_reasons_chart()
            canvas5 = FigureCanvas(fig5)
            canvas5.setMinimumHeight(300)
            canvas5.setMaximumHeight(400)
            
            chart5_group = QGroupBox("🚫 Motivos de Denegación")
            chart5_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e293b; padding-top: 10px; }")
            chart5_layout = QVBoxLayout(chart5_group)
            chart5_layout.setContentsMargins(10, 15, 10, 10)
            chart5_layout.addWidget(canvas5)
            layout.addWidget(chart5_group)
        except Exception as e:
            print(f"Error creando gráfica de denegaciones: {e}")
    
    def refresh_stats(self):
        """Actualiza todas las estadísticas."""
        # Limpiar y recrear la interfaz
        QMessageBox.information(self, "Actualizar", 
                               "♻️ Actualizando estadísticas...\n\n"
                               "Cierra y vuelve a abrir esta pestaña para ver los datos actualizados.")
    
    def export_charts(self):
        """Exporta las gráficas como imágenes."""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportar")
        
        if folder:
            try:
                # Crear gráficas y guardar
                charts = [
                    ('accesos_por_hora.png', self.analytics.create_hourly_access_chart()),
                    ('accesos_diarios.png', self.analytics.create_daily_access_chart()),
                    ('top_usuarios.png', self.analytics.create_top_users_chart()),
                    ('distribucion_confianza.png', self.analytics.create_confidence_distribution()),
                    ('motivos_denegacion.png', self.analytics.create_denial_reasons_chart()),
                ]
                
                for filename, fig in charts:
                    filepath = os.path.join(folder, filename)
                    fig.savefig(filepath, dpi=300, bbox_inches='tight')
                
                QMessageBox.information(self, "Exportación Exitosa",
                                       f"✅ Se exportaron 5 gráficas a:\n{folder}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Error al exportar: {e}")


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================

class ProfessionalMainWindow(QMainWindow):
    """Ventana principal con diseño profesional."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sistema de Control de Acceso con IA')
        self.resize(1280, 820)
        
        # Inicializar sistemas
        self.face_system = FacialRecognitionSystem()
        self.db = DatabaseManager()
        self.access_system = AccessControlSystem()
        
        self.init_ui()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 2px solid #e2e8f0;
                min-height: 80px;
                max-height: 80px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        logo_label = QLabel("🤖")
        logo_label.setStyleSheet("font-size: 42px;")
        header_layout.addWidget(logo_label)
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Control de Acceso con IA")
        title_label.setObjectName("headerTitle")
        
        subtitle_label = QLabel("Sistema de Reconocimiento Facial")
        subtitle_label.setStyleSheet("color: #64748b; font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        
        self.access_view = AccessView(self.access_system)
        self.register_view = RegisterView(self.face_system, self.db)
        self.history_view = HistoryView(self.db)
        self.statistics_view = StatisticsView(self.db)
        self.ai_analysis_view = AIAnalysisView(self.face_system)
        self.settings_view = SettingsView(self.face_system, self.db)
        
        # Conectar señales
        self.register_view.registered.connect(self.on_user_registered)
        
        tabs.addTab(self.access_view, "🎥 Verificación de Acceso")
        tabs.addTab(self.register_view, "👤 Registro de Usuarios")
        tabs.addTab(self.history_view, "📊 Historial")
        tabs.addTab(self.statistics_view, "📈 Estadísticas")
        tabs.addTab(self.ai_analysis_view, "🧠 Análisis de IA")
        tabs.addTab(self.settings_view, "⚙️ Configuración")
        
        layout.addWidget(tabs)
    
    def on_user_registered(self):
        """Se ejecuta cuando se registra un usuario."""
        self.access_view.update_users_count()
        self.history_view.refresh()
    
    def closeEvent(self, event):
        # Detener cámaras
        if hasattr(self.access_view, 'video') and self.access_view.video:
            self.access_view.stop_camera()
        if hasattr(self.register_view, 'video') and self.register_view.video:
            self.register_view.stop_camera()
        if hasattr(self.ai_analysis_view, 'video') and self.ai_analysis_view.video:
            self.ai_analysis_view.stop_analysis()
        event.accept()


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(PROFESSIONAL_STYLE)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ProfessionalMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
