"""
Zentrales Design-System für alle Grafiken.

Hier stehen Farben und Layout EINMAL - jede Seite greift darauf zu.
Wenn du das Aussehen ändern willst, änderst du nur diese Datei.
"""

import plotly.graph_objects as go

# --------------------------------------------------------------------
# FARBROLLEN
# --------------------------------------------------------------------
# Sequenziell (Menge): EIN Farbton von hell nach dunkel.
# Divergierend (Vorzeichen): zwei Pole + neutrales Grau in der Mitte.
# Kategorial (Identität): feste Reihenfolge, niemals zyklisch wiederholen.

SEQ_LOW = "#cde2fb"
SEQ_MID = "#2a78d6"
SEQ_HIGH = "#0d366b"

DIV_LOW = "#2a78d6"   # blau  - weniger / unter dem Normalwert
DIV_MID = "#f0efec"   # neutrales grau
DIV_HIGH = "#d03b3b"  # rot   - mehr / über dem Normalwert

# Kategoriale Palette: diese Reihenfolge ist auf Farbsehschwäche
# geprüft. Immer von vorne nach hinten vergeben, nie umsortieren.
CATEGORICAL = [
    "#2a78d6",  # blau
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # gelb
    "#e87ba4",  # magenta
    "#008300",  # grün
    "#4a3aa7",  # violett
    "#e34948",  # rot
]

# Flächen & Schrift
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"

# Plotly-Farbskalen
SCALE_SEQ = [[0.0, SEQ_LOW], [0.5, SEQ_MID], [1.0, SEQ_HIGH]]
SCALE_DIV = [[0.0, DIV_LOW], [0.5, DIV_MID], [1.0, DIV_HIGH]]

FONT = "Inter, Helvetica Neue, Helvetica, Arial, sans-serif"


def style(fig: go.Figure, title: str = "", subtitle: str = "",
          source: str = "Datenquelle: Statistik Austria – data.statistik.gv.at",
          height: int = 520, showlegend: bool | None = None) -> go.Figure:
    """Einheitliches Layout auf eine Plotly-Figur anwenden."""

    kopf = f"<b>{title}</b>"
    if subtitle:
        kopf += (
            f"<br><span style='font-size:13px;color:{INK_SECONDARY};"
            f"font-weight:400'>{subtitle}</span>"
        )

    fig.update_layout(
        title=dict(text=kopf, x=0, xanchor="left",
                   font=dict(size=20, color=INK_PRIMARY, family=FONT),
                   pad=dict(b=18)),
        font=dict(family=FONT, size=13, color=INK_SECONDARY),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        height=height,
        margin=dict(l=10, r=10, t=95, b=70),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family=FONT,
                        bordercolor=GRID),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.0,
                    xanchor="left", x=0, title_text=""),
    )
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)

    fig.update_xaxes(showgrid=False, zeroline=False,
                     linecolor=GRID, ticks="outside", tickcolor=GRID,
                     title_font=dict(size=12, color=INK_MUTED),
                     tickfont=dict(size=12, color=INK_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1,
                     zeroline=False, linecolor="rgba(0,0,0,0)",
                     title_font=dict(size=12, color=INK_MUTED),
                     tickfont=dict(size=12, color=INK_MUTED))

    if source:
        fig.add_annotation(
            text=source, showarrow=False,
            xref="paper", yref="paper", x=0, y=-0.16,
            xanchor="left", yanchor="top",
            font=dict(size=11, color=INK_MUTED),
        )
    return fig


def kennzahl(label: str, wert: str, hinweis: str = "") -> str:
    """HTML für eine große Kennzahl-Kachel."""
    return f"""
    <div style="background:{SURFACE};border:1px solid {GRID};
                border-radius:12px;padding:18px 20px;height:100%">
      <div style="font-size:12px;color:{INK_MUTED};
                  text-transform:uppercase;letter-spacing:.06em">{label}</div>
      <div style="font-size:34px;font-weight:700;color:{INK_PRIMARY};
                  line-height:1.15;margin-top:6px">{wert}</div>
      <div style="font-size:12px;color:{INK_SECONDARY};margin-top:4px">{hinweis}</div>
    </div>
    """
