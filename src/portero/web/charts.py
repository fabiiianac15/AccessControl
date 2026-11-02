"""Gráfica de barras en SVG generada en el servidor: sin librerías ni JavaScript."""

from __future__ import annotations

from markupsafe import Markup, escape

WIDTH, HEIGHT = 720, 168
LEFT, RIGHT, TOP, BOTTOM = 8, 8, 12, 24
# Fuera de este rango solo se dibuja si hubo movimiento: la madrugada vacía no aporta.
DEFAULT_START, DEFAULT_END = 6, 21


def hourly_bars(hours: list[dict], current_hour: int) -> Markup:
    active = [h["hour"] for h in hours if h["granted"] or h["denied"]]
    first = min([DEFAULT_START, *active])
    last = max([DEFAULT_END, *active])
    visible = hours[first : last + 1]
    peak = max((h["granted"] + h["denied"] for h in visible), default=0) or 1

    plot_height = HEIGHT - TOP - BOTTOM
    slot = (WIDTH - LEFT - RIGHT) / len(visible)
    width = max(slot - 4, 2)
    baseline = HEIGHT - BOTTOM
    parts = [
        f'<svg class="chart" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-labelledby="chart-title">'
        '<title id="chart-title">Accesos por hora de hoy</title>'
        f'<line class="chart-axis" x1="{LEFT}" x2="{WIDTH - RIGHT}" '
        f'y1="{baseline}" y2="{baseline}"/>'
    ]
    for index, hour in enumerate(visible):
        x = LEFT + index * slot + 2
        granted_h = hour["granted"] / peak * plot_height
        denied_h = hour["denied"] / peak * plot_height
        label = f"{hour['hour']:02d}:00: {hour['granted']} concedidos, {hour['denied']} denegados"
        parts.append(f"<g><title>{escape(label)}</title>")
        if hour["hour"] == current_hour:
            parts.append(
                f'<rect class="chart-now" x="{x - 2:.1f}" y="{TOP}" '
                f'width="{slot:.1f}" height="{plot_height}"/>'
            )
        if granted_h:
            parts.append(
                f'<rect class="chart-granted" x="{x:.1f}" y="{baseline - granted_h:.1f}" '
                f'width="{width:.1f}" height="{granted_h:.1f}" rx="1.5"/>'
            )
        if denied_h:
            # Separación de 2 px entre segmentos para distinguirlos también sin color.
            top = baseline - granted_h - denied_h - (2 if granted_h else 0)
            parts.append(
                f'<rect class="chart-denied" x="{x:.1f}" y="{top:.1f}" '
                f'width="{width:.1f}" height="{denied_h:.1f}" rx="1.5"/>'
            )
        parts.append("</g>")
        if hour["hour"] % 3 == 0:
            parts.append(
                f'<text class="chart-label" x="{x + width / 2:.1f}" y="{HEIGHT - 7}" '
                f'text-anchor="middle">{hour["hour"]:02d}</text>'
            )
    parts.append("</svg>")
    return Markup("".join(parts))  # noqa: S704 - valores numéricos propios y etiquetas escapadas
