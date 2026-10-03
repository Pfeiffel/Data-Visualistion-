"""Tourismus: Saisonalität und Herkunftsländer seit 1973."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src import data as d
from src.theme import (CATEGORICAL, GRID, INK_SECONDARY, SCALE_SEQ, SEQ_HIGH,
                       SURFACE, kennzahl, style)

st.set_page_config(page_title="Tourismus · Österreich in Daten",
                   page_icon="📊", layout="wide")
st.markdown(f"<style>.stApp{{background:{SURFACE}}}"
            f".block-container{{max-width:1180px;padding-top:2.5rem}}</style>",
            unsafe_allow_html=True)

st.title("Tourismus")
st.markdown(
    f"<p style='color:{INK_SECONDARY};font-size:17px;max-width:46em'>"
    "Nächtigungen seit November 1973 – der längste Datensatz in diesem "
    "Dashboard. Österreich enthält zwei völlig verschiedene Tourismusländer: "
    "eines, das vom Winter lebt, und eines, das vom Sommer lebt.</p>",
    unsafe_allow_html=True)

with st.spinner("Über 50 Jahre Nächtigungsdaten werden geladen …"):
    roh = d.tourismus()

SAMMEL = ("insgesamt|zusammen|gesamt|übrige|sonstige|unbekannt|"
          "^Ausland$|^Inland$|Europa$|Welt")

laender_echt = sorted(
    x for x in roh["land"].dropna().unique()
    if not pd.Series([x]).str.contains(SAMMEL, case=False, regex=True).iloc[0]
)
bundeslaender = sorted(
    x for x in roh["bundesland"].dropna().unique()
    if not pd.Series([x]).str.contains("insgesamt|gesamt|Österreich",
                                       case=False, regex=True).iloc[0]
)

with st.sidebar:
    st.markdown("### Filter")
    j_min, j_max = int(roh["jahr"].min()), int(roh["jahr"].max())
    zeitraum = st.slider("Zeitraum", j_min, j_max, (max(j_min, 2000), j_max))
    kennzahl_wahl = st.radio("Kennzahl", ["Nächtigungen", "Ankünfte"])

spalte = "naechtigungen" if kennzahl_wahl == "Nächtigungen" else "ankuenfte"
df = roh[roh["jahr"].between(*zeitraum)]

# ------------------------------------------------------------ Kennzahlen
gesamt = df[spalte].sum()
pro_jahr = df.groupby("jahr")[spalte].sum()
sommer = df[df["monat"].between(6, 9)][spalte].sum()
winter = df[df["monat"].isin([12, 1, 2, 3])][spalte].sum()

k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    st.markdown(kennzahl(kennzahl_wahl + " gesamt",
                         f"{gesamt / 1e6:,.0f} Mio.".replace(",", "."),
                         f"{zeitraum[0]}–{zeitraum[1]}"),
                unsafe_allow_html=True)
with k2:
    st.markdown(kennzahl("Sommer gegen Winter",
                         f"{sommer / winter:.2f} : 1",
                         "Juni–September zu Dezember–März"),
                unsafe_allow_html=True)
with k3:
    bestes = pro_jahr.idxmax()
    st.markdown(kennzahl("Stärkstes Jahr", str(int(bestes)),
                         f"{pro_jahr.max() / 1e6:,.1f} Mio."
                         .replace(",", ".")),
                unsafe_allow_html=True)

st.write("")
st.write("")

# ------------------------------------------------- Saisonalität je Land
st.subheader("Winterland oder Sommerland?")

auswahl_bl = st.multiselect(
    "Bundesländer vergleichen", bundeslaender,
    default=[b for b in bundeslaender
             if any(k in b for k in ("Tirol", "Kärnten", "Salzburg",
                                     "Wien", "Burgenland"))][:5],
    label_visibility="collapsed")

if auswahl_bl:
    saison = (df[df["bundesland"].isin(auswahl_bl)]
              .groupby(["bundesland", "jahr", "monat"], as_index=False)[spalte]
              .sum())
    saison["anteil"] = (saison.groupby(["bundesland", "jahr"])[spalte]
                              .transform(lambda s: s / s.sum() * 100))
    profil = (saison.groupby(["bundesland", "monat"], as_index=False)["anteil"]
                    .mean())

    sf = go.Figure()
    for i, bl in enumerate(auswahl_bl):
        teil = profil[profil["bundesland"] == bl].sort_values("monat")
        sf.add_trace(go.Scatter(
            x=[d.MONATE[m - 1] for m in teil["monat"]], y=teil["anteil"],
            name=bl, mode="lines+markers",
            line=dict(width=3, color=CATEGORICAL[i % 8], shape="spline"),
            marker=dict(size=7),
            hovertemplate="%{x}<br><b>%{y:.1f} %</b> der Jahresnächtigungen"
                          f"<extra>{bl}</extra>"))
    sf.add_hline(y=100 / 12, line=dict(color=GRID, width=1, dash="dash"),
                 annotation_text="gleichmäßiges Jahr",
                 annotation_font=dict(size=11, color="#898781"))
    sf.update_yaxes(title="Anteil am Jahr", ticksuffix=" %")

    st.plotly_chart(
        style(sf, "Das Jahr im Profil",
              f"Anteil jedes Monats an den {kennzahl_wahl.lower()} des Jahres, "
              f"Durchschnitt {zeitraum[0]}–{zeitraum[1]}", height=500),
        use_container_width=True)

# ------------------------------------------------------ Herkunftsländer
st.write("")
st.subheader("Woher die Gäste kommen")

anzahl = st.slider("Wie viele Länder anzeigen?", 3, 12, 8)

nach_land = (df[df["land"].isin(laender_echt)]
             .groupby(["jahr", "land"], as_index=False)[spalte].sum())
top_laender = (nach_land.groupby("land")[spalte].sum()
                        .nlargest(anzahl).index.tolist())

lf = go.Figure()
for i, land in enumerate(top_laender):
    teil = nach_land[nach_land["land"] == land].sort_values("jahr")
    lf.add_trace(go.Scatter(
        x=teil["jahr"], y=teil[spalte] / 1e6, name=land,
        mode="lines", line=dict(width=2.6, color=CATEGORICAL[i % 8]),
        hovertemplate="%{x}<br><b>%{y:.2f} Mio.</b>"
                      f"<extra>{land}</extra>"))
lf.update_yaxes(title=f"{kennzahl_wahl} in Millionen")

st.plotly_chart(
    style(lf, "Die wichtigsten Herkunftsländer",
          "Ein Blick auf 50 Jahre Zeitgeschichte – Ostöffnung, Billigflüge, "
          "Pandemie", height=520),
    use_container_width=True)

# ---------------------------------------------------- Heatmap Jahr/Monat
with st.expander("Der Tourismus-Kalender"):
    bl_karte = st.selectbox("Bundesland", ["Ganz Österreich"] + bundeslaender)
    q = df if bl_karte == "Ganz Österreich" else df[df["bundesland"] == bl_karte]

    gitter = q.groupby(["jahr", "monat"], as_index=False)[spalte].sum()
    gitter["anteil"] = (gitter.groupby("jahr")[spalte]
                              .transform(lambda s: s / s.sum() * 100))
    matrix = gitter.pivot(index="jahr", columns="monat", values="anteil")

    hm = go.Figure(go.Heatmap(
        z=matrix.values, x=[d.MONATE[m - 1] for m in matrix.columns],
        y=matrix.index, colorscale=SCALE_SEQ, xgap=1, ygap=1,
        colorbar=dict(title=dict(text="% des Jahres", side="right"),
                      thickness=14, len=0.75, outlinewidth=0),
        hovertemplate="%{y} · %{x}<br><b>%{z:.1f} %</b> des Jahres"
                      "<extra></extra>"))
    hm.update_yaxes(autorange="reversed", dtick=5, showgrid=False)
    st.plotly_chart(
        style(hm, f"Saisonmuster: {bl_karte}",
              "Anteil jedes Monats am jeweiligen Jahr", height=620),
        use_container_width=True)

    st.download_button(
        "Daten als CSV", gitter.to_csv(index=False).encode("utf-8"),
        file_name="tourismus_saison.csv", mime="text/csv")
