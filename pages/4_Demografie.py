"""Demografie: Fertilität nach Alter und Lebenserwartung."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import data as d
from src.theme import (CATEGORICAL, DIV_HIGH, GRID, INK_MUTED, INK_SECONDARY,
                       SEQ_HIGH, SEQ_LOW, SURFACE, kennzahl, style)

st.set_page_config(page_title="Demografie · Österreich in Daten",
                   page_icon="📊", layout="wide")
st.markdown(f"<style>.stApp{{background:{SURFACE}}}"
            f".block-container{{max-width:1180px;padding-top:2.5rem}}</style>",
            unsafe_allow_html=True)

st.title("Demografie")
st.markdown(
    f"<p style='color:{INK_SECONDARY};font-size:17px;max-width:46em'>"
    "Zwei Datensätze, die nach einzelnen Lebensjahren aufgeschlüsselt sind – "
    "und damit Fragen beantworten, die gröbere Altersgruppen verschlucken."
    "</p>", unsafe_allow_html=True)


def mischfarbe(anteil: float) -> str:
    """Zwischen zwei Hex-Farben interpolieren (für den Zeitverlauf)."""
    a = tuple(int(SEQ_LOW[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(SEQ_HIGH[i:i + 2], 16) for i in (1, 3, 5))
    c = [round(a[i] + (b[i] - a[i]) * anteil) for i in range(3)]
    return f"rgb({c[0]},{c[1]},{c[2]})"


tab_geburt, tab_leben = st.tabs(["Kinderkriegen", "Lebenserwartung"])

# =========================================================== FERTILITÄT
with tab_geburt:
    with st.spinner("Fertilitätsdaten werden geladen …"):
        fert = d.fertilitaet()

    regionen = sorted(fert["region"].dropna().unique())
    at_name = next((r for r in regionen
                    if "österreich" in str(r).lower()), regionen[0])

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        region = st.selectbox("Region", regionen,
                              index=regionen.index(at_name))
    with c2:
        j_min, j_max = int(fert["jahr"].min()), int(fert["jahr"].max())
        spanne = st.slider("Zeitraum", j_min, j_max, (j_min, j_max),
                           key="fert_jahre")

    f = fert[(fert["region"] == region)
             & fert["jahr"].between(*spanne)
             & fert["alter"].between(15, 48)]

    if f.empty:
        st.warning("Keine Daten für diese Auswahl.")
        st.stop()

    # Mit der Rate gewichtetes Durchschnittsalter der Mütter
    schnitt = (f.groupby("jahr")
                .apply(lambda g: np.average(g["alter"], weights=g["rate"]),
                       include_groups=False)
                .rename("alter").reset_index())

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        st.markdown(kennzahl("Durchschnittsalter heute",
                             f"{schnitt['alter'].iloc[-1]:.1f} Jahre",
                             f"im Jahr {int(schnitt['jahr'].iloc[-1])}"),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(kennzahl("Verschiebung",
                             f"+{schnitt['alter'].iloc[-1] - schnitt['alter'].iloc[0]:.1f} Jahre",
                             f"seit {int(schnitt['jahr'].iloc[0])}"),
                    unsafe_allow_html=True)
    with k3:
        letztes = f[f["jahr"] == f["jahr"].max()]
        haeufigstes = letztes.loc[letztes["rate"].idxmax(), "alter"]
        st.markdown(kennzahl("Häufigstes Alter", f"{int(haeufigstes)} Jahre",
                             "mit der höchsten Geburtenrate"),
                    unsafe_allow_html=True)

    st.write("")

    # Ein Linienprofil je Jahr, eingefärbt von hell (früh) nach dunkel (spät)
    jahre = sorted(f["jahr"].unique())
    rf = go.Figure()
    for jahr in jahre:
        teil = f[f["jahr"] == jahr].sort_values("alter")
        anteil = (jahr - jahre[0]) / max(1, (jahre[-1] - jahre[0]))
        rf.add_trace(go.Scatter(
            x=teil["alter"], y=teil["rate"], name=str(jahr), mode="lines",
            line=dict(width=2.2 if jahr in (jahre[0], jahre[-1]) else 1.3,
                      color=mischfarbe(anteil)),
            showlegend=jahr in (jahre[0], jahre[-1]),
            hovertemplate="Alter %{x}<br><b>%{y:.1f}</b> Geburten je 1.000 Frauen"
                          f"<extra>{jahr}</extra>"))
    rf.update_xaxes(title="Alter der Mutter", dtick=5)
    rf.update_yaxes(title="Geburten je 1.000 Frauen")

    st.plotly_chart(
        style(rf, "Der Berg wandert nach rechts",
              f"Geburtenrate nach Alter, ein Profil je Jahr – {region}. "
              "Helle Linien sind frühe Jahre, dunkle die jüngsten.",
              height=520),
        use_container_width=True)

    # Durchschnittsalter als eigene Kurve
    sf = go.Figure(go.Scatter(
        x=schnitt["jahr"], y=schnitt["alter"], mode="lines+markers",
        line=dict(width=3.5, color=SEQ_HIGH), marker=dict(size=7),
        hovertemplate="%{x}<br><b>%{y:.2f} Jahre</b><extra></extra>",
        showlegend=False))
    sf.update_yaxes(title="Durchschnittsalter der Mütter")
    st.plotly_chart(
        style(sf, "Jahr für Jahr ein bisschen später",
              "Mit der Geburtenrate gewichtetes Durchschnittsalter",
              height=420),
        use_container_width=True)

# ====================================================== LEBENSERWARTUNG
with tab_leben:
    with st.spinner("Lebenserwartung wird geladen …"):
        leb = d.lebenserwartung()

    regionen_l = sorted(leb["region"].dropna().unique())
    at_l = next((r for r in regionen_l
                 if "österreich" in str(r).lower()), regionen_l[0])

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        region_l = st.selectbox("Region", regionen_l,
                                index=regionen_l.index(at_l), key="leb_region")
    with c2:
        jahre_l = sorted(leb["jahr"].unique())
        jahr_l = st.select_slider("Jahr", jahre_l, value=jahre_l[-1])

    aktuell = leb[(leb["region"] == region_l) & (leb["jahr"] == jahr_l)
                  & (leb["alter"] <= 95)].copy()
    aktuell["endalter"] = aktuell["alter"] + aktuell["restjahre"]

    bei_geburt = aktuell[aktuell["alter"] == 0]

    k1, k2, k3 = st.columns(3, gap="medium")
    for spalte, (_, zeile) in zip([k1, k2], bei_geburt.iterrows()):
        with spalte:
            st.markdown(kennzahl(f"Lebenserwartung {zeile['geschlecht']}",
                                 f"{zeile['restjahre']:.1f} Jahre",
                                 "bei der Geburt"), unsafe_allow_html=True)
    with k3:
        if len(bei_geburt) >= 2:
            abstand = abs(bei_geburt["restjahre"].iloc[0]
                          - bei_geburt["restjahre"].iloc[1])
            st.markdown(kennzahl("Unterschied", f"{abstand:.1f} Jahre",
                                 "zwischen den Geschlechtern"),
                        unsafe_allow_html=True)

    st.write("")

    ef = go.Figure()
    for i, gesch in enumerate(sorted(aktuell["geschlecht"].dropna().unique())):
        teil = aktuell[aktuell["geschlecht"] == gesch].sort_values("alter")
        ef.add_trace(go.Scatter(
            x=teil["alter"], y=teil["endalter"], name=str(gesch),
            mode="lines", line=dict(width=3.5, color=CATEGORICAL[i % 8]),
            hovertemplate="Mit %{x} Jahren<br>erwartetes Endalter: "
                          "<b>%{y:.1f}</b>" f"<extra>{gesch}</extra>"))
    ef.add_trace(go.Scatter(
        x=[0, 95], y=[0, 95], mode="lines", name="heutiges Alter",
        line=dict(width=1, color=GRID, dash="dash"), hoverinfo="skip"))
    ef.update_xaxes(title="Aktuelles Alter", dtick=10)
    ef.update_yaxes(title="Erwartetes Endalter")

    st.plotly_chart(
        style(ef, "Je älter du wirst, desto älter wirst du",
              f"Aktuelles Alter plus fernere Lebenserwartung – {region_l}, "
              f"{jahr_l}", height=520),
        use_container_width=True)

    st.caption(
        "Klingt paradox, ist aber logisch: Wer 80 geworden ist, hat alle "
        "Risiken davor bereits überlebt. Deshalb liegt das erwartete "
        "Endalter eines 80-Jährigen deutlich über dem eines Neugeborenen."
    )

    # Schere über die Zeit
    verlauf = (leb[(leb["region"] == region_l) & (leb["alter"] == 0)]
               .pivot_table(index="jahr", columns="geschlecht",
                            values="restjahre").reset_index())

    if verlauf.shape[1] >= 3:
        g1, g2 = verlauf.columns[1], verlauf.columns[2]
        scf = go.Figure()
        scf.add_trace(go.Scatter(x=verlauf["jahr"], y=verlauf[g1],
                                 mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"))
        scf.add_trace(go.Scatter(x=verlauf["jahr"], y=verlauf[g2],
                                 mode="lines", line=dict(width=0),
                                 fill="tonexty",
                                 fillcolor="rgba(42,120,214,0.14)",
                                 showlegend=False, hoverinfo="skip"))
        for i, g in enumerate([g1, g2]):
            scf.add_trace(go.Scatter(
                x=verlauf["jahr"], y=verlauf[g], name=str(g),
                mode="lines+markers",
                line=dict(width=3.2, color=CATEGORICAL[i % 8]),
                marker=dict(size=6),
                hovertemplate="%{x}<br><b>%{y:.1f} Jahre</b>"
                              f"<extra>{g}</extra>"))
        scf.update_yaxes(title="Lebenserwartung bei der Geburt")
        st.plotly_chart(
            style(scf, "Die Schere schließt sich",
                  "Die Fläche zwischen den Linien ist der Unterschied",
                  height=460),
            use_container_width=True)
