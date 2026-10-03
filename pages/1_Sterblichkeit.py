"""Sterblichkeit: Saisonalität und Übersterblichkeit."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import data as d
from src.theme import (CATEGORICAL, DIV_HIGH, DIV_LOW, GRID, INK_SECONDARY,
                       SCALE_DIV, SCALE_SEQ, SURFACE, kennzahl, style)

st.set_page_config(page_title="Sterblichkeit · Österreich in Daten",
                   page_icon="📊", layout="wide")
st.markdown(f"<style>.stApp{{background:{SURFACE}}}"
            f".block-container{{max-width:1180px;padding-top:2.5rem}}</style>",
            unsafe_allow_html=True)

st.title("Sterblichkeit")
st.markdown(
    f"<p style='color:{INK_SECONDARY};font-size:17px;max-width:46em'>"
    "Wöchentliche Sterbefälle seit 2000, nach Bundesland, Altersgruppe und "
    "Geschlecht. Die Rohzahlen steigen über die Jahre schon deshalb, weil "
    "Österreich mehr und ältere Einwohner hat – deshalb lässt sich unten "
    "auf relative Darstellungen umschalten.</p>",
    unsafe_allow_html=True)

with st.spinner("Daten werden von Statistik Austria geladen …"):
    roh = d.sterbefaelle()

# ---------------------------------------------------------------- Filter
with st.sidebar:
    st.markdown("### Filter")

    bundeslaender = sorted(roh["bundesland"].dropna().unique())
    auswahl_bl = st.multiselect("Bundesland", bundeslaender,
                                default=bundeslaender,
                                help="Leer lassen = ganz Österreich")

    altersgruppen = sorted(roh["altersgruppe"].dropna().unique())
    auswahl_alter = st.multiselect("Altersgruppe", altersgruppen,
                                   default=altersgruppen)

    geschlechter = sorted(roh["geschlecht"].dropna().unique())
    auswahl_gesch = st.multiselect("Geschlecht", geschlechter,
                                   default=geschlechter)

    j_min, j_max = int(roh["jahr"].min()), int(roh["jahr"].max())
    zeitraum = st.slider("Zeitraum", j_min, j_max, (j_min, j_max))

df = roh.copy()
if auswahl_bl:
    df = df[df["bundesland"].isin(auswahl_bl)]
if auswahl_alter:
    df = df[df["altersgruppe"].isin(auswahl_alter)]
if auswahl_gesch:
    df = df[df["geschlecht"].isin(auswahl_gesch)]
df = df[df["jahr"].between(*zeitraum)]

if df.empty:
    st.warning("Für diese Filterkombination gibt es keine Daten.")
    st.stop()

wochen = (df.groupby(["jahr", "woche"], as_index=False)["tote"].sum()
            .sort_values(["jahr", "woche"]))

# ------------------------------------------------------------ Kennzahlen
jahres_summe = wochen.groupby("jahr")["tote"].sum()
winter = wochen[wochen["woche"].isin([1, 2, 3, 4, 5, 50, 51, 52])]["tote"].mean()
sommer = wochen[wochen["woche"].between(26, 35)]["tote"].mean()
spitze = wochen.loc[wochen["tote"].idxmax()]

k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    st.markdown(kennzahl("Sterbefälle gesamt",
                         f"{int(jahres_summe.sum()):,}".replace(",", "."),
                         f"{zeitraum[0]}–{zeitraum[1]}"),
                unsafe_allow_html=True)
with k2:
    st.markdown(kennzahl("Winter gegen Sommer",
                         f"+{(winter / sommer - 1) * 100:.0f} %",
                         "mehr Tote pro Woche im Winter"),
                unsafe_allow_html=True)
with k3:
    st.markdown(kennzahl("Schlimmste Woche",
                         f"{int(spitze['tote']):,}".replace(",", "."),
                         f"KW {int(spitze['woche'])} / {int(spitze['jahr'])}"),
                unsafe_allow_html=True)

st.write("")
st.write("")

# ------------------------------------------------------------- Heatmap
st.subheader("Der Sterblichkeits-Kalender")

modus = st.radio(
    "Darstellung",
    ["Absolute Zahlen", "Relativ zum eigenen Jahr", "Übersterblichkeit"],
    horizontal=True, label_visibility="collapsed",
    help=(
        "Absolut zeigt die Rohzahlen – dort überlagert der Alterungstrend "
        "die Saisonalität. Relativ normiert jedes Jahr auf seinen eigenen "
        "Schnitt. Übersterblichkeit vergleicht jede Woche mit derselben "
        "Woche der fünf Jahre davor."
    ),
)

tab = wochen.copy()

if modus == "Absolute Zahlen":
    tab["wert"] = tab["tote"]
    skala, mitte, einheit = SCALE_SEQ, None, "Tote"
    untertitel = "Sterbefälle je Kalenderwoche"

elif modus == "Relativ zum eigenen Jahr":
    tab["wert"] = (tab.groupby("jahr")["tote"]
                      .transform(lambda s: s / s.mean() * 100))
    skala, mitte, einheit = SCALE_DIV, 100, "% des Jahresschnitts"
    untertitel = "Jede Zeile auf ihren eigenen Jahresschnitt normiert"

else:
    tab = tab.sort_values(["woche", "jahr"])
    tab["basis"] = (tab.groupby("woche")["tote"]
                       .transform(lambda s: s.shift(1).rolling(5).mean()))
    tab["wert"] = (tab["tote"] - tab["basis"]) / tab["basis"] * 100
    tab = tab.dropna(subset=["wert"])
    skala, mitte, einheit = SCALE_DIV, 0, "% Abweichung"
    untertitel = "Vergleich mit derselben Woche der fünf Jahre davor"

if tab.empty:
    st.info("Für diese Auswahl reicht der Zeitraum nicht für eine "
            "Vergleichsbasis. Bitte den Zeitraum erweitern.")
else:
    matrix = tab.pivot(index="jahr", columns="woche", values="wert")

    heat = go.Figure(go.Heatmap(
        z=matrix.values,
        x=matrix.columns,
        y=matrix.index,
        colorscale=skala,
        zmid=mitte,
        xgap=1, ygap=1,
        colorbar=dict(title=dict(text=einheit, side="right"),
                      thickness=14, len=0.75, outlinewidth=0),
        hovertemplate=("Jahr %{y} · KW %{x}<br>"
                       "<b>%{z:.1f}</b> " + einheit + "<extra></extra>"),
    ))
    heat.update_yaxes(autorange="reversed", dtick=2, showgrid=False)
    heat.update_xaxes(title="Kalenderwoche", dtick=5)
    st.plotly_chart(
        style(heat, "Wann Österreich stirbt", untertitel, height=640),
        use_container_width=True)

# -------------------------------------------------------- Jahresprofil
st.write("")
st.subheader("Das Jahr im Profil")

profil_quelle = df.copy()
profil_quelle["index"] = (
    profil_quelle.groupby(["jahr", "altersgruppe"])["tote"]
    .transform(lambda s: s / s.mean() * 100))

nach_alter = (profil_quelle.groupby(["altersgruppe", "woche"], as_index=False)
                           ["index"].mean())

linien = go.Figure()
for i, gruppe in enumerate(sorted(nach_alter["altersgruppe"].unique())):
    teil = nach_alter[nach_alter["altersgruppe"] == gruppe]
    linien.add_trace(go.Scatter(
        x=teil["woche"], y=teil["index"], name=str(gruppe),
        mode="lines", line=dict(width=3, color=CATEGORICAL[i % 8]),
        hovertemplate="KW %{x}<br><b>%{y:.0f} %</b> des Jahresschnitts"
                      "<extra>" + str(gruppe) + "</extra>",
    ))
linien.add_hline(y=100, line=dict(color=GRID, width=1, dash="dash"))
linien.update_xaxes(title="Kalenderwoche", dtick=5)
linien.update_yaxes(title="% des Jahresschnitts", ticksuffix=" %")

st.plotly_chart(
    style(linien, "Der Winter trifft nicht alle gleich",
          "Sterbefälle je Woche in Prozent des Jahresschnitts der jeweiligen "
          "Altersgruppe, gemittelt über alle gewählten Jahre", height=480),
    use_container_width=True)

st.caption(
    "Die Saisonalität ist fast ausschließlich ein Phänomen der Älteren – "
    "bei den Jüngeren verläuft das Jahr deutlich flacher."
)

# ------------------------------------------------------------- Tabelle
with st.expander("Die extremsten Wochen anzeigen"):
    if modus == "Übersterblichkeit" and not tab.empty:
        top = (tab.nlargest(15, "wert")
                  [["jahr", "woche", "tote", "basis", "wert"]]
                  .rename(columns={"tote": "Sterbefälle",
                                   "basis": "erwartet",
                                   "wert": "Abweichung %"}))
        top["erwartet"] = top["erwartet"].round(0)
        top["Abweichung %"] = top["Abweichung %"].round(1)
        st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        top = (wochen.nlargest(15, "tote")
                     .rename(columns={"tote": "Sterbefälle"}))
        st.dataframe(top, use_container_width=True, hide_index=True)

    st.download_button(
        "Gefilterte Daten als CSV",
        wochen.to_csv(index=False).encode("utf-8"),
        file_name="sterbefaelle_gefiltert.csv",
        mime="text/csv",
    )
