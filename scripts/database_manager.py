"""
Sistema de Base de Datos y Logging para Auditoría
Gestiona logs de acceso, eventos del sistema y reportes
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import csv

class DatabaseManager:
    def __init__(self, db_path="access_control.db"):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Crear carpetas necesarias para el proyecto
        self._create_project_folders()
        
        # Inicializar base de datos
        self.connect()
        self.create_tables()
    
    def _create_project_folders(self):
        """Crea las carpetas necesarias del proyecto si no existen"""
        folders = [
            'access_photos/usuarios_registrados',
            'access_photos/accesos_concedidos',
            'access_photos/accesos_denegados',
            'access_photos/intrusos',
            'access_photos/registros_fallidos',
            'temp_images',
            'exports',
        ]
        
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
        
        print(f"[v0] Carpetas del proyecto verificadas/creadas")
    
    def connect(self):
        """Conecta a la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"[v0] Conectado a base de datos: {self.db_path}")
        except Exception as e:
            print(f"[v0] Error al conectar a base de datos: {e}")
    
    def create_tables(self):
        """Crea las tablas necesarias en la base de datos"""
        try:
            # Tabla de logs de acceso
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_name TEXT,
                    access_granted INTEGER NOT NULL,
                    confidence REAL,
                    method TEXT,
                    reason TEXT,
                    metadata TEXT,
                    image_path TEXT
                )
            ''')
            
            # Tabla de eventos del sistema
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    user_name TEXT,
                    details TEXT
                )
            ''')
            
            # Tabla de usuarios (metadata adicional)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT UNIQUE NOT NULL,
                    role TEXT,
                    department TEXT,
                    access_level INTEGER,
                    registered_at TEXT,
                    last_access TEXT,
                    total_accesses INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            # Índices para mejorar rendimiento
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_access_timestamp 
                ON access_logs(timestamp)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_access_user 
                ON access_logs(user_name)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON system_events(timestamp)
            ''')
            
            self.conn.commit()
            print("[v0] Tablas de base de datos inicializadas")
        except Exception as e:
            print(f"[v0] Error al crear tablas: {e}")
    
    def log_access_attempt(self, result):
        """
        Registra un intento de acceso
        
        Args:
            result: Diccionario con resultado de verificación de acceso
        """
        try:
            self.cursor.execute('''
                INSERT INTO access_logs 
                (timestamp, user_name, access_granted, confidence, method, reason, metadata, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('timestamp', datetime.now().isoformat()),
                result.get('user', 'Desconocido'),
                1 if result.get('access_granted', False) else 0,
                result.get('confidence'),
                result.get('method', 'unknown'),
                result.get('reason', ''),
                json.dumps(result.get('metadata', {})),
                result.get('image_path', '')
            ))
            
            # Actualizar contador de accesos del usuario si fue exitoso
            if result.get('access_granted', False) and result.get('user'):
                self.cursor.execute('''
                    UPDATE users_metadata 
                    SET last_access = ?, total_accesses = total_accesses + 1
                    WHERE user_name = ?
                ''', (datetime.now().isoformat(), result.get('user')))
            
            self.conn.commit()
            print(f"[v0] Log de acceso registrado: {result.get('user', 'Desconocido')}")
        except Exception as e:
            print(f"[v0] Error al registrar log de acceso: {e}")
    
    def log_system_event(self, event_type, description, user_name=None, details=None):
        """
        Registra un evento del sistema
        
        Args:
            event_type: Tipo de evento (registro, eliminación, configuración, etc.)
            description: Descripción del evento
            user_name: Usuario relacionado (opcional)
            details: Detalles adicionales (opcional)
        """
        try:
            self.cursor.execute('''
                INSERT INTO system_events 
                (timestamp, event_type, description, user_name, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                description,
                user_name,
                json.dumps(details) if details else None
            ))
            
            self.conn.commit()
            print(f"[v0] Evento del sistema registrado: {event_type}")
        except Exception as e:
            print(f"[v0] Error al registrar evento: {e}")
    
    def sync_user_metadata(self, name, metadata):
        """
        Sincroniza metadata de usuario con la base de datos
        
        Args:
            name: Nombre del usuario
            metadata: Diccionario con metadata del usuario
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users_metadata 
                (user_name, role, department, access_level, registered_at, active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                name,
                metadata.get('role', 'Usuario'),
                metadata.get('department', 'General'),
                int(metadata.get('access_level', 1)),
                metadata.get('registered_at', datetime.now().isoformat())
            ))
            
            self.conn.commit()
            print(f"[v0] Metadata sincronizada para usuario: {name}")
        except Exception as e:
            print(f"[v0] Error al sincronizar metadata: {e}")
    
    def get_access_logs(self, limit=50, user_name=None, date_from=None, date_to=None):
        """
        Obtiene logs de acceso con filtros opcionales
        
        Args:
            limit: Número máximo de registros
            user_name: Filtrar por usuario
            date_from: Fecha inicial (formato ISO)
            date_to: Fecha final (formato ISO)
            
        Returns:
            Lista de logs de acceso
        """
        try:
            query = "SELECT * FROM access_logs WHERE 1=1"
            params = []
            
            if user_name:
                query += " AND user_name = ?"
                params.append(user_name)
            
            if date_from:
                query += " AND timestamp >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND timestamp <= ?"
                params.append(date_to)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            
            columns = [desc[0] for desc in self.cursor.description]
            logs = []
            
            for row in self.cursor.fetchall():
                log = dict(zip(columns, row))
                if log['metadata']:
                    log['metadata'] = json.loads(log['metadata'])
                logs.append(log)
            
            return logs
        except Exception as e:
            print(f"[v0] Error al obtener logs: {e}")
            return []
    
    def get_system_events(self, limit=50, event_type=None):
        """
        Obtiene eventos del sistema
        
        Args:
            limit: Número máximo de registros
            event_type: Filtrar por tipo de evento
            
        Returns:
            Lista de eventos
        """
        try:
            query = "SELECT * FROM system_events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            
            columns = [desc[0] for desc in self.cursor.description]
            events = []
            
            for row in self.cursor.fetchall():
                event = dict(zip(columns, row))
                if event['details']:
                    event['details'] = json.loads(event['details'])
                events.append(event)
            
            return events
        except Exception as e:
            print(f"[v0] Error al obtener eventos: {e}")
            return []
    
    def get_user_statistics(self, user_name):
        """
        Obtiene estadísticas de un usuario
        
        Args:
            user_name: Nombre del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Obtener metadata del usuario
            self.cursor.execute('''
                SELECT * FROM users_metadata WHERE user_name = ?
            ''', (user_name,))
            
            user_data = self.cursor.fetchone()
            
            if not user_data:
                return None
            
            columns = [desc[0] for desc in self.cursor.description]
            stats = dict(zip(columns, user_data))
            
            # Obtener estadísticas de acceso
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN access_granted = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN access_granted = 0 THEN 1 ELSE 0 END) as denied,
                    AVG(CASE WHEN confidence IS NOT NULL THEN confidence ELSE 0 END) as avg_confidence
                FROM access_logs
                WHERE user_name = ?
            ''', (user_name,))
            
            access_stats = self.cursor.fetchone()
            
            stats['total_attempts'] = access_stats[0]
            stats['successful_accesses'] = access_stats[1]
            stats['denied_accesses'] = access_stats[2]
            stats['avg_confidence'] = access_stats[3]
            
            return stats
        except Exception as e:
            print(f"[v0] Error al obtener estadísticas: {e}")
            return None
    
    def generate_report(self, report_type='daily', output_file=None):
        """
        Genera un reporte de actividad
        
        Args:
            report_type: Tipo de reporte ('daily', 'weekly', 'monthly')
            output_file: Archivo de salida (opcional, formato CSV)
            
        Returns:
            Diccionario con datos del reporte
        """
        try:
            # Calcular rango de fechas
            now = datetime.now()
            
            if report_type == 'daily':
                date_from = (now - timedelta(days=1)).isoformat()
                title = "Reporte Diario"
            elif report_type == 'weekly':
                date_from = (now - timedelta(weeks=1)).isoformat()
                title = "Reporte Semanal"
            elif report_type == 'monthly':
                date_from = (now - timedelta(days=30)).isoformat()
                title = "Reporte Mensual"
            else:
                date_from = None
                title = "Reporte Completo"
            
            # Obtener estadísticas generales
            query = "SELECT COUNT(*) FROM access_logs"
            params = []
            
            if date_from:
                query += " WHERE timestamp >= ?"
                params.append(date_from)
            
            self.cursor.execute(query, params)
            total_attempts = self.cursor.fetchone()[0]
            
            # Accesos concedidos y denegados
            query = """
                SELECT 
                    SUM(CASE WHEN access_granted = 1 THEN 1 ELSE 0 END) as granted,
                    SUM(CASE WHEN access_granted = 0 THEN 1 ELSE 0 END) as denied
                FROM access_logs
            """
            
            if date_from:
                query += " WHERE timestamp >= ?"
            
            self.cursor.execute(query, params)
            granted, denied = self.cursor.fetchone()
            
            # Usuarios más activos
            query = """
                SELECT user_name, COUNT(*) as accesses
                FROM access_logs
                WHERE access_granted = 1
            """
            
            if date_from:
                query += " AND timestamp >= ?"
            
            query += " GROUP BY user_name ORDER BY accesses DESC LIMIT 10"
            
            self.cursor.execute(query, params)
            top_users = self.cursor.fetchall()
            
            # Horarios de mayor actividad
            query = """
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as accesses
                FROM access_logs
            """
            
            if date_from:
                query += " WHERE timestamp >= ?"
            
            query += " GROUP BY hour ORDER BY hour"
            
            self.cursor.execute(query, params)
            hourly_activity = self.cursor.fetchall()
            
            report = {
                'title': title,
                'generated_at': now.isoformat(),
                'period': report_type,
                'date_from': date_from,
                'date_to': now.isoformat(),
                'total_attempts': total_attempts,
                'granted': granted or 0,
                'denied': denied or 0,
                'success_rate': (granted / total_attempts * 100) if total_attempts > 0 else 0,
                'top_users': [{'user': u[0], 'accesses': u[1]} for u in top_users],
                'hourly_activity': [{'hour': h[0], 'accesses': h[1]} for h in hourly_activity]
            }
            
            # Guardar a CSV si se especifica
            if output_file:
                self.export_report_to_csv(report, output_file)
            
            return report
        except Exception as e:
            print(f"[v0] Error al generar reporte: {e}")
            return None
    
    def export_report_to_csv(self, report, output_file):
        """
        Exporta un reporte a formato CSV
        
        Args:
            report: Diccionario con datos del reporte
            output_file: Ruta del archivo de salida
        """
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Encabezado
                writer.writerow([report['title']])
                writer.writerow(['Generado:', report['generated_at']])
                writer.writerow(['Período:', report['period']])
                writer.writerow([])
                
                # Estadísticas generales
                writer.writerow(['Estadísticas Generales'])
                writer.writerow(['Total de intentos:', report['total_attempts']])
                writer.writerow(['Accesos concedidos:', report['granted']])
                writer.writerow(['Accesos denegados:', report['denied']])
                writer.writerow(['Tasa de éxito:', f"{report['success_rate']:.2f}%"])
                writer.writerow([])
                
                # Usuarios más activos
                writer.writerow(['Usuarios Más Activos'])
                writer.writerow(['Usuario', 'Accesos'])
                for user in report['top_users']:
                    writer.writerow([user['user'], user['accesses']])
                writer.writerow([])
                
                # Actividad por hora
                writer.writerow(['Actividad por Hora'])
                writer.writerow(['Hora', 'Accesos'])
                for activity in report['hourly_activity']:
                    writer.writerow([f"{activity['hour']}:00", activity['accesses']])
            
            print(f"[v0] Reporte exportado a: {output_file}")
        except Exception as e:
            print(f"[v0] Error al exportar reporte: {e}")
    
    def print_report(self, report):
        """
        Imprime un reporte en consola
        
        Args:
            report: Diccionario con datos del reporte
        """
        print("\n" + "=" * 70)
        print(f"{report['title'].upper()}")
        print("=" * 70)
        print(f"Generado: {report['generated_at']}")
        print(f"Período: {report['period']}")
        print("=" * 70)
        
        print("\nESTADÍSTICAS GENERALES")
        print("-" * 70)
        print(f"Total de intentos de acceso: {report['total_attempts']}")
        print(f"Accesos concedidos: {report['granted']}")
        print(f"Accesos denegados: {report['denied']}")
        print(f"Tasa de éxito: {report['success_rate']:.2f}%")
        
        print("\nUSUARIOS MÁS ACTIVOS")
        print("-" * 70)
        for i, user in enumerate(report['top_users'][:5], 1):
            print(f"{i}. {user['user']}: {user['accesses']} accesos")
        
        print("\nACTIVIDAD POR HORA")
        print("-" * 70)
        for activity in report['hourly_activity']:
            bar = "█" * (activity['accesses'] // 2)
            print(f"{activity['hour']}:00 | {bar} ({activity['accesses']})")
        
        print("=" * 70)
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            print("[v0] Conexión a base de datos cerrada")


if __name__ == "__main__":
    # Ejemplo de uso
    db = DatabaseManager()
    
    print("\n[v0] Sistema de base de datos inicializado")
    print("[v0] Importa este módulo para usar el sistema de logging")
