"""Wohnen: Häuserpreise gegen Löhne, und wo gebaut wird."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import data as d
from src.theme import (CATEGORICAL, DIV_HIGH, GRID, INK_SECONDARY, SCALE_SEQ,
                       SEQ_HIGH, SEQ_LOW, SURFACE, kennzahl, style)

st.set_page_config(page_title="Wohnen · Österreich in Daten",
                   page_icon="📊", layout="wide")
st.markdown(f"<style>.stApp{{background:{SURFACE}}}"
            f".block-container{{max-width:1180px;padding-top:2.5rem}}</style>",
            unsafe_allow_html=True)

st.title("Wohnen")
st.markdown(
    f"<p style='color:{INK_SECONDARY};font-size:17px;max-width:46em'>"
    "Zwei Fragen: Sind die Löhne mit den Immobilienpreisen mitgegangen – "
    "und wo in Österreich wird eigentlich gebaut?</p>",
    unsafe_allow_html=True)

tab_preise, tab_bau = st.tabs(["Preise und Löhne", "Wo gebaut wird"])

# ====================================================== PREISE UND LÖHNE
with tab_preise:
    with st.spinner("Daten werden geladen …"):
        hpi = d.haeuserpreise()
        lohn = d.tariflohn()

    gemeinsam = hpi.merge(lohn, on="jahr", suffixes=("_haus", "_lohn"))

    if gemeinsam.empty:
        st.warning("Die beiden Reihen überschneiden sich zeitlich nicht.")
        st.stop()

    jahre = sorted(gemeinsam["jahr"].unique())
    basis = st.select_slider(
        "Basisjahr – auf dieses Jahr werden beide Reihen auf 100 gesetzt",
        options=jahre, value=jahre[0])

    g = gemeinsam.copy()
    g["haus"] = g["index_haus"] / g.loc[g["jahr"] == basis,
                                        "index_haus"].iloc[0] * 100
    g["lohn"] = g["index_lohn"] / g.loc[g["jahr"] == basis,
                                        "index_lohn"].iloc[0] * 100
    g["kaufkraft"] = g["lohn"] / g["haus"] * 100

    letzte = g.iloc[-1]

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        st.markdown(kennzahl("Häuserpreise",
                             f"+{letzte['haus'] - 100:.0f} %",
                             f"seit {basis}"), unsafe_allow_html=True)
    with k2:
        st.markdown(kennzahl("Tariflöhne",
                             f"+{letzte['lohn'] - 100:.0f} %",
                             f"seit {basis}"), unsafe_allow_html=True)
    with k3:
        st.markdown(kennzahl("Kaufkraft",
                             f"{letzte['kaufkraft']:.0f} %",
                             "eines Gehalts, gemessen in Immobilien"),
                    unsafe_allow_html=True)

    st.write("")

    fig = go.Figure()
    # Fläche zwischen den Linien
    fig.add_trace(go.Scatter(x=g["jahr"], y=g["haus"], mode="lines",
                             line=dict(width=0), showlegend=False,
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=g["jahr"], y=g["lohn"], mode="lines",
                             line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(208,59,59,0.12)",
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=g["jahr"], y=g["haus"], name="Häuserpreise", mode="lines+markers",
        line=dict(width=3.5, color=DIV_HIGH), marker=dict(size=7),
        hovertemplate="%{x}<br><b>%{y:.1f}</b><extra>Häuserpreise</extra>"))
    fig.add_trace(go.Scatter(
        x=g["jahr"], y=g["lohn"], name="Tariflöhne", mode="lines+markers",
        line=dict(width=3.5, color=CATEGORICAL[0]), marker=dict(size=7),
        hovertemplate="%{x}<br><b>%{y:.1f}</b><extra>Tariflöhne</extra>"))
    fig.add_hline(y=100, line=dict(color=GRID, width=1, dash="dash"))
    fig.update_yaxes(title=f"Index ({basis} = 100)")

    st.plotly_chart(
        style(fig, "Häuser laufen den Löhnen davon",
              "Beide Reihen auf ein gemeinsames Basisjahr umgerechnet – nur "
              "so sind sie vergleichbar. Die Fläche ist die Lücke.",
              height=500),
        use_container_width=True)

    st.caption(
        "Hinweis: Tariflöhne sind kollektivvertraglich vereinbarte Löhne, "
        "nicht die tatsächlich ausbezahlten Gehälter."
    )

    with st.expander("Kaufkraft als eigene Kurve"):
        kf = go.Figure()
        kf.add_trace(go.Scatter(
            x=g["jahr"], y=g["kaufkraft"], mode="lines+markers",
            line=dict(width=3.5, color=DIV_HIGH), marker=dict(size=7),
            fill="tozeroy", fillcolor="rgba(208,59,59,0.10)",
            hovertemplate="%{x}<br><b>%{y:.0f} %</b><extra></extra>",
            showlegend=False))
        kf.add_hline(y=100, line=dict(color=GRID, width=1, dash="dash"))
        kf.update_yaxes(title="", ticksuffix=" %")
        st.plotly_chart(
            style(kf, "Ein Gehalt kauft immer weniger Quadratmeter",
                  f"Löhne im Verhältnis zu Häuserpreisen, {basis} = 100 %",
                  height=420),
            use_container_width=True)

# ========================================================= WO GEBAUT WIRD
with tab_bau:
    with st.spinner("Baubewilligungen werden geladen …"):
        bau = d.baubewilligungen()

    st.markdown(
        f"<p style='color:{INK_SECONDARY}'>Bewilligte Wohnungen je Bezirk "
        "seit 2010. Achtung: Der Datensatz nutzt Bezirks-Ordnungszahlen, "
        "keine Gemeindekennziffern – die Zuordnung läuft deshalb über "
        "Namen.</p>", unsafe_allow_html=True)

    regionen = sorted(bau["region"].dropna().unique())

    # Oberösterreichs Bezirke über Namen finden
    OOE = ["Linz", "Steyr", "Wels", "Braunau", "Eferding", "Freistadt",
           "Gmunden", "Grieskirchen", "Kirchdorf", "Linz-Land", "Perg",
           "Ried", "Rohrbach", "Schärding", "Steyr-Land",
           "Urfahr", "Vöcklabruck", "Wels-Land"]
    ooe_treffer = [r for r in regionen
                   if any(r.lower().startswith(o.lower()) for o in OOE)]

    c1, c2 = st.columns([2, 1], gap="large")
    with c1:
        voreinstellung = ooe_treffer if ooe_treffer else regionen[:8]
        auswahl = st.multiselect("Bezirke", regionen, default=voreinstellung)
    with c2:
        j_min, j_max = int(bau["jahr"].min()), int(bau["jahr"].max())
        spanne = st.slider("Zeitraum", j_min, j_max, (j_min, j_max))

    if not auswahl:
        st.info("Bitte mindestens einen Bezirk auswählen.")
        st.stop()

    # "insgesamt"-Codes finden, damit nichts doppelt gezählt wird
    cl_art = d.codeliste("baubewilligung", "C-ARTBAU-0")
    cl_wohn = d.codeliste("baubewilligung", "C-WOHNART4-0")
    code_art = d.finde_code(cl_art, "insgesamt|gesamt")
    code_wohn = d.finde_code(cl_wohn, "insgesamt|gesamt")

    b = bau[bau["region"].isin(auswahl) & bau["jahr"].between(*spanne)]
    gesamt = b.copy()
    if code_art:
        gesamt = gesamt[gesamt["artbau_code"] == code_art]
    if code_wohn:
        gesamt = gesamt[gesamt["wohnart_code"] == code_wohn]

    # ---------------------------------------------------- Rangliste
    rang = (gesamt.groupby("region", as_index=False)["wohnungen"].sum()
                  .sort_values("wohnungen"))

    balken = go.Figure(go.Bar(
        x=rang["wohnungen"], y=rang["region"], orientation="h",
        marker=dict(color=rang["wohnungen"], colorscale=SCALE_SEQ,
                    showscale=False),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} Wohnungen<extra></extra>",
    ))
    balken.update_xaxes(title="Bewilligte Wohnungen")
    balken.update_yaxes(showgrid=False)
    st.plotly_chart(
        style(balken, "Wo gebaut wurde",
              f"Bewilligte Wohnungen insgesamt, {spanne[0]} bis {spanne[1]}",
              height=max(380, 26 * len(rang) + 180)),
        use_container_width=True)

    # ---------------------------------------------------- Zeitverlauf
    verlauf = (gesamt.groupby(["jahr", "region"], as_index=False)["wohnungen"]
                     .sum())
    top = (rang.nlargest(6, "wohnungen")["region"].tolist())

    lf = go.Figure()
    for i, reg in enumerate(top):
        teil = verlauf[verlauf["region"] == reg]
        lf.add_trace(go.Scatter(
            x=teil["jahr"], y=teil["wohnungen"], name=reg, mode="lines+markers",
            line=dict(width=3, color=CATEGORICAL[i % 8]), marker=dict(size=6),
            hovertemplate="%{x}<br><b>%{y:,.0f}</b> Wohnungen"
                          f"<extra>{reg}</extra>"))
    lf.update_yaxes(title="Bewilligte Wohnungen")
    st.plotly_chart(
        style(lf, "Entwicklung über die Zeit",
              "Die sechs Bezirke mit den meisten Bewilligungen in der Auswahl",
              height=470),
        use_container_width=True)

    # ------------------------------------------------- Haus oder Wohnung
    typen = b.copy()
    if code_art:
        typen = typen[typen["artbau_code"] == code_art]
    if code_wohn:
        typen = typen[typen["wohnart_code"] != code_wohn]
    typen = (typen.groupby(["jahr", "wohnart"], as_index=False)["wohnungen"]
                  .sum().dropna(subset=["wohnart"]))

    if not typen.empty:
        typen["anteil"] = (typen.groupby("jahr")["wohnungen"]
                                .transform(lambda s: s / s.sum() * 100))
        af = go.Figure()
        for i, art in enumerate(sorted(typen["wohnart"].unique())):
            teil = typen[typen["wohnart"] == art]
            af.add_trace(go.Scatter(
                x=teil["jahr"], y=teil["anteil"], name=str(art)[:40],
                mode="lines", stackgroup="eins",
                line=dict(width=0.5, color=CATEGORICAL[i % 8]),
                fillcolor=CATEGORICAL[i % 8],
                hovertemplate="%{x}<br><b>%{y:.1f} %</b>"
                              f"<extra>{str(art)[:40]}</extra>"))
        af.update_yaxes(title="", ticksuffix=" %", range=[0, 100])
        st.plotly_chart(
            style(af, "Haus oder Wohnung?",
                  "Anteil der bewilligten Wohnungen nach Gebäudetyp",
                  height=460),
            use_container_width=True)

    with st.expander("Daten herunterladen"):
        st.dataframe(rang.sort_values("wohnungen", ascending=False),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "Als CSV", gesamt.to_csv(index=False).encode("utf-8"),
            file_name="baubewilligungen.csv", mime="text/csv")
