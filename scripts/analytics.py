"""
Módulo de Análisis y Gráficas con Matplotlib
- Gráficas de accesos por hora
- Estadísticas de usuarios
- Análisis de intentos fallidos
- Reportes visuales
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from datetime import datetime, timedelta
from collections import Counter
import numpy as np


class AccessAnalytics:
    """Generador de gráficas y estadísticas."""
    
    def __init__(self, db_path: str = "access_control.db"):
        self.db_path = db_path
    
    def get_access_logs(self, days: int = 7) -> list:
        """Obtiene logs de los últimos N días."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT timestamp, user_name, access_granted, confidence, reason
            FROM access_logs
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (date_limit,))
        
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    def create_hourly_access_chart(self) -> Figure:
        """Gráfica de accesos por hora del día."""
        logs = self.get_access_logs(days=7)
        
        # Extraer horas
        hours = []
        for log in logs:
            if log[2]:  # Solo accesos concedidos
                timestamp = datetime.fromisoformat(log[0])
                hours.append(timestamp.hour)
        
        # Contar por hora
        hour_counts = Counter(hours)
        all_hours = range(24)
        counts = [hour_counts.get(h, 0) for h in all_hours]
        
        # Crear gráfica
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        bars = ax.bar(all_hours, counts, color='#3b82f6', alpha=0.7)
        
        # Resaltar horas pico
        max_count = max(counts) if counts else 0
        for i, (hour, count) in enumerate(zip(all_hours, counts)):
            if count == max_count and count > 0:
                bars[i].set_color('#10b981')
        
        ax.set_xlabel('Hora del Día', fontsize=12, fontweight='bold')
        ax.set_ylabel('Número de Accesos', fontsize=12, fontweight='bold')
        ax.set_title('Distribución de Accesos por Hora (Últimos 7 Días)', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(all_hours)
        ax.set_xticklabels([f'{h:02d}:00' for h in all_hours], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        fig.tight_layout()
        return fig
    
    def create_daily_access_chart(self) -> Figure:
        """Gráfica de accesos por día."""
        logs = self.get_access_logs(days=30)
        
        # Separar por resultado
        granted_dates = []
        denied_dates = []
        
        for log in logs:
            timestamp = datetime.fromisoformat(log[0])
            date = timestamp.date()
            
            if log[2]:  # Concedido
                granted_dates.append(date)
            else:  # Denegado
                denied_dates.append(date)
        
        # Contar por día
        granted_counts = Counter(granted_dates)
        denied_counts = Counter(denied_dates)
        
        # Últimos 30 días
        dates = [(datetime.now().date() - timedelta(days=i)) for i in range(30)]
        dates.reverse()
        
        granted_values = [granted_counts.get(d, 0) for d in dates]
        denied_values = [denied_counts.get(d, 0) for d in dates]
        
        # Crear gráfica
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        x = np.arange(len(dates))
        width = 0.35
        
        ax.bar(x - width/2, granted_values, width, label='Concedidos', 
              color='#10b981', alpha=0.8)
        ax.bar(x + width/2, denied_values, width, label='Denegados', 
              color='#ef4444', alpha=0.8)
        
        ax.set_xlabel('Fecha', fontsize=12, fontweight='bold')
        ax.set_ylabel('Número de Accesos', fontsize=12, fontweight='bold')
        ax.set_title('Accesos Diarios (Últimos 30 Días)', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x[::3])  # Mostrar cada 3 días
        ax.set_xticklabels([d.strftime('%d/%m') for d in dates[::3]], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        fig.tight_layout()
        return fig
    
    def create_top_users_chart(self, limit: int = 10) -> Figure:
        """Gráfica de usuarios más activos."""
        logs = self.get_access_logs(days=30)
        
        # Contar por usuario (solo accesos concedidos)
        users = [log[1] for log in logs if log[2]]
        user_counts = Counter(users).most_common(limit)
        
        if not user_counts:
            # Gráfica vacía
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   ha='center', va='center', fontsize=14)
            return fig
        
        names = [uc[0] for uc in user_counts]
        counts = [uc[1] for uc in user_counts]
        
        # Crear gráfica
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        bars = ax.barh(names, counts, color='#3b82f6', alpha=0.7)
        
        # Degradado de colores
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(names)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xlabel('Número de Accesos', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {limit} Usuarios Más Activos (Últimos 30 Días)', 
                    fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis='x')
        
        # Agregar valores en las barras
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.5, i, str(count), va='center')
        
        fig.tight_layout()
        return fig
    
    def create_confidence_distribution(self) -> Figure:
        """Distribución de niveles de confianza."""
        logs = self.get_access_logs(days=30)
        
        # Extraer confidencias (solo accesos concedidos)
        confidences = [log[3] * 100 for log in logs if log[2] and log[3] is not None]
        
        if not confidences:
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   ha='center', va='center', fontsize=14)
            return fig
        
        # Crear gráfica
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        n, bins, patches = ax.hist(confidences, bins=20, color='#3b82f6', 
                                   alpha=0.7, edgecolor='black')
        
        # Colorear según nivel de confianza
        for i, patch in enumerate(patches):
            bin_center = (bins[i] + bins[i+1]) / 2
            if bin_center >= 90:
                patch.set_facecolor('#10b981')
            elif bin_center >= 70:
                patch.set_facecolor('#f59e0b')
            else:
                patch.set_facecolor('#ef4444')
        
        ax.set_xlabel('Confianza (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frecuencia', fontsize=12, fontweight='bold')
        ax.set_title('Distribución de Niveles de Confianza', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Línea vertical para promedio
        avg = np.mean(confidences)
        ax.axvline(avg, color='red', linestyle='--', linewidth=2, 
                  label=f'Promedio: {avg:.1f}%')
        ax.legend()
        
        fig.tight_layout()
        return fig
    
    def create_denial_reasons_chart(self) -> Figure:
        """Gráfica de motivos de denegación."""
        logs = self.get_access_logs(days=30)
        
        # Contar razones de denegación
        reasons = [log[4] for log in logs if not log[2] and log[4]]
        reason_counts = Counter(reasons)
        
        if not reason_counts:
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No hay accesos denegados', 
                   ha='center', va='center', fontsize=14)
            return fig
        
        # Crear gráfica de pastel
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        labels = list(reason_counts.keys())
        sizes = list(reason_counts.values())
        colors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors[:len(labels)],
                                           startangle=90)
        
        # Mejorar legibilidad
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_title('Motivos de Accesos Denegados', 
                    fontsize=14, fontweight='bold')
        
        fig.tight_layout()
        return fig
    
    def get_summary_stats(self) -> dict:
        """Resumen de estadísticas."""
        logs = self.get_access_logs(days=30)
        
        total = len(logs)
        granted = sum(1 for log in logs if log[2])
        denied = total - granted
        
        # Calcular promedio de confianza
        confidences = [log[3] for log in logs if log[2] and log[3] is not None]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        # Usuarios únicos
        unique_users = len(set(log[1] for log in logs if log[2]))
        
        # Accesos hoy
        today = datetime.now().date()
        today_accesses = sum(1 for log in logs 
                            if datetime.fromisoformat(log[0]).date() == today and log[2])
        
        return {
            'total_accesos': total,
            'accesos_concedidos': granted,
            'accesos_denegados': denied,
            'tasa_exito': (granted / total * 100) if total > 0 else 0,
            'confianza_promedio': avg_confidence * 100 if avg_confidence else 0,
            'usuarios_unicos': unique_users,
            'accesos_hoy': today_accesses
        }
