"""
Österreich in Daten – Startseite.

Starten mit:   streamlit run app.py
"""

import streamlit as st

from src.theme import GRID, INK_MUTED, INK_SECONDARY, SURFACE

st.set_page_config(
    page_title="Österreich in Daten",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: {SURFACE}; }}
      .block-container {{ padding-top: 3rem; max-width: 1180px; }}
      h1, h2, h3 {{ letter-spacing: -0.02em; }}
      section[data-testid="stSidebar"] {{
          background: #ffffff; border-right: 1px solid {GRID};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Österreich in Daten")
st.markdown(
    f"<p style='font-size:18px;color:{INK_SECONDARY};max-width:48em;"
    f"margin-top:-8px'>Interaktive Auswertungen aus dem offenen Datenbestand "
    f"von Statistik Austria. Alle Daten werden direkt von der Quelle geladen "
    f"und sind damit immer aktuell.</p>",
    unsafe_allow_html=True,
)

st.write("")

seiten = [
    ("Sterblichkeit",
     "Wöchentliche Sterbefälle seit dem Jahr 2000. Warum Österreich im "
     "Winter stirbt – und welche Wochen aus dem Rahmen fielen.",
     "pages/1_Sterblichkeit.py"),
    ("Wohnen",
     "Häuserpreise gegen Löhne, und wo in Österreich tatsächlich gebaut "
     "wird. Mit Schwerpunkt Oberösterreich.",
     "pages/2_Wohnen.py"),
    ("Tourismus",
     "Nächtigungen seit 1973. Winterland oder Sommerland – und woher die "
     "Gäste kommen.",
     "pages/3_Tourismus.py"),
    ("Demografie",
     "Wann Österreich Kinder bekommt und wie alt es dabei wird.",
     "pages/4_Demografie.py"),
]

spalten = st.columns(2, gap="large")
for i, (titel, text, ziel) in enumerate(seiten):
    with spalten[i % 2]:
        with st.container(border=True):
            st.subheader(titel)
            st.markdown(
                f"<p style='color:{INK_SECONDARY};min-height:4.5em'>{text}</p>",
                unsafe_allow_html=True,
            )
            st.page_link(ziel, label="Öffnen", icon="→")

st.write("")
st.divider()

st.markdown(
    f"""
    <p style='color:{INK_MUTED};font-size:13px'>
    Datenquelle: <b>Statistik Austria</b> – data.statistik.gv.at, lizenziert
    unter CC BY 4.0. Kartengrundlage: GeoJSON-TopoJSON-Austria.<br>
    Die Datensätze werden beim ersten Aufruf heruntergeladen und
    anschließend 24 Stunden zwischengespeichert – der erste Seitenaufruf
    dauert deshalb etwas länger.
    </p>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Über dieses Dashboard")
    st.caption(
        "Gebaut mit Streamlit und Plotly. Es liegen keine Datendateien im "
        "Repository – alles kommt zur Laufzeit von Statistik Austria."
    )
    if st.button("Zwischenspeicher leeren", use_container_width=True):
        st.cache_data.clear()
        st.success("Daten werden beim nächsten Aufruf neu geladen.")
