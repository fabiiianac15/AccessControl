"""
GUI del Sistema de Control de Acceso con IA
- Vista de cámara en vivo y verificación
- Registro de usuarios desde imagen o cámara
- Visualización de logs
- Configuración básica

Requisitos: PyQt6, OpenCV, face_recognition, dlib
Ejecutar: python scripts/gui_app.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import face_recognition

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QImage, QPixmap, QAction
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFileDialog, QSpinBox, QComboBox, QFormLayout, QLineEdit,
    QTextEdit, QMessageBox, QMainWindow, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter
)

# Importar módulos del proyecto (al ejecutar desde raíz o scripts/)
try:
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager
except ModuleNotFoundError:
    # Ajustar sys.path para permitir importar desde scripts/
    sys.path.append(str(Path(__file__).resolve().parent))
    from face_recognition_system import FacialRecognitionSystem
    from access_control import AccessControlSystem
    from database_manager import DatabaseManager


def cvimg_to_qpixmap(frame: np.ndarray) -> QPixmap:
    """Convierte un frame BGR de OpenCV a QPixmap para PyQt."""
    if frame is None:
        return QPixmap()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


class CameraView(QWidget):
    """Widget que muestra la cámara con reconocimiento en vivo."""
    def __init__(self, access_system: AccessControlSystem, parent=None):
        super().__init__(parent)
        self.access_system = access_system
        self.face_system = access_system.face_system
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.current_result = None
        self.required_level = 1
        self.camera_index = 0

        # UI
        self.video_label = QLabel("Cámara no inicializada")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 360)

        self.status_label = QLabel("Estado: listo")
        self.status_label.setWordWrap(True)

        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)
        self.level_spin.valueChanged.connect(self._on_level_changed)

        self.camera_combo = QComboBox()
        # Asumimos 2 cámaras máximo; el usuario puede ajustar
        self.camera_combo.addItems(["Cámara 0", "Cámara 1"])
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)

        self.start_btn = QPushButton("Iniciar cámara")
        self.start_btn.clicked.connect(self.start_camera)
        self.stop_btn = QPushButton("Detener")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Nivel requerido:"))
        top_bar.addWidget(self.level_spin)
        top_bar.addSpacing(16)
        top_bar.addWidget(QLabel("Cámara:"))
        top_bar.addWidget(self.camera_combo)
        top_bar.addStretch()
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.stop_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)

    def _on_level_changed(self, v: int):
        self.required_level = v

    def _on_camera_changed(self, idx: int):
        self.camera_index = idx
        if self.timer.isActive():
            self.restart_camera()

    def start_camera(self):
        try:
            self.video = cv2.VideoCapture(self.camera_index)
            if not self.video.isOpened():
                raise RuntimeError("No se pudo acceder a la cámara")
            self.timer.start(30)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"Estado: cámara iniciada (nivel requerido {self.required_level})")
        except Exception as e:
            QMessageBox.critical(self, "Error de cámara", str(e))

    def stop_camera(self):
        self.timer.stop()
        if self.video:
            self.video.release()
            self.video = None
        self.video_label.setText("Cámara detenida")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def restart_camera(self):
        self.stop_camera()
        self.start_camera()

    def update_frame(self):
        if self.video is None:
            return
        ok, frame = self.video.read()
        if not ok or frame is None:
            self.status_label.setText("Estado: error al capturar frame")
            return

        # Voltear horizontalmente para efecto espejo natural
        frame = cv2.flip(frame, 1)

        # Reconocimiento en vivo (similar a verify_access_realtime, pero sin bloquear)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        status_text = "Esperando rostro..."
        status_color = (255, 255, 255)

        for (top, right, bottom, left), enc in zip(locations, encodings):
            name = "Desconocido"
            confidence = 0.0
            color = (0, 0, 255)  # rojo por defecto

            if len(self.face_system.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(
                    self.face_system.known_face_encodings, enc, tolerance=self.face_system.tolerance
                )
                distances = face_recognition.face_distance(self.face_system.known_face_encodings, enc)

                if len(distances) > 0:
                    best_idx = int(np.argmin(distances))
                    if matches[best_idx]:
                        name = self.face_system.known_face_names[best_idx]
                        confidence = float(1 - distances[best_idx])
                        meta = self.face_system.known_face_metadata[best_idx]
                        user_level = int(meta.get('access_level', 1))

                        if user_level >= self.required_level:
                            color = (0, 255, 0)  # verde
                            status_text = f"ACCESO CONCEDIDO - {name} ({confidence:.0%})"
                            status_color = (0, 255, 0)
                            # Loguear solo la primera vez por sesión de arranque
                            if not self.current_result:
                                self._log_access(True, name, confidence, meta, method='realtime')
                                self.current_result = True
                        else:
                            color = (0, 165, 255)  # naranja
                            status_text = f"ACCESO DENEGADO - {name} (nivel insuficiente)"
                            status_color = (255, 165, 0)
                            if not self.current_result:
                                self._log_access(False, name, confidence, meta, reason='Nivel insuficiente', method='realtime')
                                self.current_result = True
                    else:
                        name = "Desconocido"
                        color = (0, 0, 255)
                        status_text = "Rostro desconocido"
                        status_color = (255, 0, 0)
            else:
                status_text = "Sin usuarios registrados"
                status_color = (255, 0, 0)

            # Dibujar
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, -1)
            label = name if confidence == 0 else f"{name} ({confidence:.0%})"
            cv2.putText(frame, label, (left + 6, bottom - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        self.video_label.setPixmap(cvimg_to_qpixmap(frame).scaled(
            self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.status_label.setText(status_text)

    def _log_access(self, granted: bool, name: str, confidence: float, meta: dict, reason: str | None = None, method: str = 'realtime'):
        result = {
            'timestamp': datetime.now().isoformat(),
            'access_granted': granted,
            'user': name if name else 'Desconocido',
            'confidence': confidence,
            'metadata': meta or {},
            'reason': reason or ('Acceso autorizado' if granted else 'Rostro no reconocido'),
            'method': method,
        }
        try:
            self.access_system.db_manager.log_access_attempt(result)
        except Exception as e:
            # No bloquear UI por errores de log
            print('[GUI] Error al registrar log de acceso:', e)


class RegisterView(QWidget):
    """Registro de usuario desde imagen o cámara."""
    def __init__(self, face_system: FacialRecognitionSystem, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.db = db
        self.video = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_preview)
        self.preview_frame = None

        # Formulario
        self.name_edit = QLineEdit()
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText('Ej: Seguridad')
        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText('Ej: TI')
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 5)
        self.level_spin.setValue(1)

        form = QFormLayout()
        form.addRow('Nombre completo:', self.name_edit)
        form.addRow('Rol/Cargo:', self.role_edit)
        form.addRow('Departamento:', self.dept_edit)
        form.addRow('Nivel de acceso:', self.level_spin)

        # Botones
        self.from_image_btn = QPushButton('Registrar desde imagen...')
        self.from_image_btn.clicked.connect(self._register_from_image)
        self.cam_toggle_btn = QPushButton('Iniciar cámara')
        self.cam_toggle_btn.clicked.connect(self._toggle_camera)
        self.capture_btn = QPushButton('Capturar y registrar')
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self._capture_and_register)

        # Vista previa
        self.preview = QLabel('Vista previa')
        self.preview.setMinimumSize(480, 270)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btns = QHBoxLayout()
        btns.addWidget(self.from_image_btn)
        btns.addStretch()
        btns.addWidget(self.cam_toggle_btn)
        btns.addWidget(self.capture_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.preview)
        layout.addLayout(btns)

    def _get_metadata(self) -> dict:
        return {
            'role': self.role_edit.text().strip() or 'Usuario',
            'department': self.dept_edit.text().strip() or 'General',
            'access_level': str(self.level_spin.value())
        }

    def _validate_name(self) -> str | None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Faltan datos', 'Ingresa el nombre completo del usuario.')
            return None
        return name

    def _register_from_image(self):
        name = self._validate_name()
        if not name:
            return
        file, _ = QFileDialog.getOpenFileName(self, 'Selecciona una imagen', str(Path.home()), 'Imágenes (*.jpg *.jpeg *.png)')
        if not file:
            return
        ok = self.face_system.register_face(name, file, self._get_metadata())
        if ok:
            self.db.sync_user_metadata(name, self._get_metadata())
            self.db.log_system_event('user_registration', f'Usuario registrado desde imagen: {name}', user_name=name, details=self._get_metadata())
            QMessageBox.information(self, 'Registro', f'Usuario {name} registrado exitosamente.')
        else:
            QMessageBox.critical(self, 'Registro', 'No se pudo registrar el usuario (rostro no detectado o ya existe).')

    def _toggle_camera(self):
        if self.timer.isActive():
            self.timer.stop()
            if self.video:
                self.video.release()
                self.video = None
            self.preview.setText('Cámara detenida')
            self.cam_toggle_btn.setText('Iniciar cámara')
            self.capture_btn.setEnabled(False)
        else:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                QMessageBox.critical(self, 'Cámara', 'No se pudo acceder a la cámara')
                return
            self.timer.start(30)
            self.cam_toggle_btn.setText('Detener cámara')
            self.capture_btn.setEnabled(True)

    def _update_preview(self):
        if not self.video:
            return
        ok, frame = self.video.read()
        if not ok:
            return
        
        # Voltear horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)
        
        self.preview_frame = frame.copy()
        self.preview.setPixmap(cvimg_to_qpixmap(frame).scaled(
            self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _capture_and_register(self):
        name = self._validate_name()
        if not name:
            return
        if self.preview_frame is None:
            QMessageBox.warning(self, 'Captura', 'No hay imagen para capturar.')
            return
        os.makedirs('temp_images', exist_ok=True)
        path = f"temp_images/{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(path, self.preview_frame)
        ok = self.face_system.register_face(name, path, self._get_metadata())
        if ok:
            self.db.sync_user_metadata(name, self._get_metadata())
            self.db.log_system_event('user_registration', f'Usuario registrado con cámara: {name}', user_name=name, details=self._get_metadata())
            QMessageBox.information(self, 'Registro', f'Usuario {name} registrado exitosamente.')
        else:
            QMessageBox.critical(self, 'Registro', 'No se pudo registrar el usuario (rostro no detectado o ya existe).')


class LogsView(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.list = QListWidget()
        self.refresh_btn = QPushButton('Actualizar')
        self.refresh_btn.clicked.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(self.refresh_btn)
        self.refresh()

    def refresh(self):
        self.list.clear()
        logs = self.db.get_access_logs(limit=100)
        for log in logs:
            status = '✅' if log['access_granted'] else '❌'
            user = log.get('user_name') or 'Desconocido'
            ts = log.get('timestamp', '')
            method = log.get('method', '')
            confidence = log.get('confidence')
            conf_str = f" ({confidence:.0%})" if confidence else ''
            item = QListWidgetItem(f"{ts} {status} {user}{conf_str} - {method}")
            self.list.addItem(item)


class SettingsView(QWidget):
    def __init__(self, face_system: FacialRecognitionSystem, parent=None):
        super().__init__(parent)
        self.face_system = face_system

        self.tol_spin = QDoubleSpinBoxCompat()
        self.tol_spin.setRange(0.3, 0.8)
        self.tol_spin.setSingleStep(0.05)
        self.tol_spin.setValue(float(self.face_system.tolerance))

        apply_btn = QPushButton('Aplicar')
        apply_btn.clicked.connect(self.apply)

        form = QFormLayout(self)
        form.addRow('Tolerancia (0.3-0.8):', self.tol_spin)
        form.addRow(apply_btn)

    def apply(self):
        tol = float(self.tol_spin.value())
        self.face_system.tolerance = tol
        QMessageBox.information(self, 'Configuración', f'Tolerancia actualizada a {tol:.2f}')


class QDoubleSpinBoxCompat(QSpinBox):
    """Compat simple usando QSpinBox como double (evitar dependencia extra)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mult = 100
        self.setRange(int(0.3 * self._mult), int(0.8 * self._mult))
        self.setSingleStep(int(0.05 * self._mult))

    def value(self):
        return super().value() / self._mult

    def setValue(self, v: float):
        super().setValue(int(v * self._mult))

    def setRange(self, a: float, b: float):
        super().setRange(int(a * self._mult), int(b * self._mult))

    def setSingleStep(self, v: float):
        super().setSingleStep(int(v * self._mult))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Control de Acceso - GUI')
        self.resize(1000, 650)

        self.face_system = FacialRecognitionSystem()
        self.db = DatabaseManager()
        self.access_system = AccessControlSystem()

        tabs = QTabWidget()
        self.camera_view = CameraView(self.access_system)
        self.register_view = RegisterView(self.face_system, self.db)
        self.logs_view = LogsView(self.db)
        self.settings_view = SettingsView(self.face_system)

        tabs.addTab(self.camera_view, 'Acceso (Cámara)')
        tabs.addTab(self.register_view, 'Registro')
        tabs.addTab(self.logs_view, 'Logs')
        tabs.addTab(self.settings_view, 'Configuración')

        self.setCentralWidget(tabs)

        # Menú simple
        self._build_menu()

    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu('Archivo')

        act_backup = QAction('Crear backup', self)
        act_backup.triggered.connect(self._create_backup)
        file_menu.addAction(act_backup)

        act_exit = QAction('Salir', self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    def _create_backup(self):
        import shutil
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('backups', exist_ok=True)
        try:
            shutil.copy2(self.face_system.database_path, f'backups/face_database_{ts}.pkl')
        except Exception as e:
            QMessageBox.warning(self, 'Backup', f'No se pudo respaldar DB de rostros: {e}')
        try:
            shutil.copy2(self.db.db_path, f'backups/access_control_{ts}.db')
        except Exception as e:
            QMessageBox.warning(self, 'Backup', f'No se pudo respaldar DB de logs: {e}')
        QMessageBox.information(self, 'Backup', 'Backup creado (ver carpeta backups/)')


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
