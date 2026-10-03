"""
Datenzugriff auf das Open-Data-Portal von Statistik Austria.

Alle Datensätze werden zur Laufzeit heruntergeladen und von Streamlit
zwischengespeichert - es liegen also KEINE Datendateien im Repository.
Beim ersten Aufruf dauert ein Datensatz ein paar Sekunden, danach
kommt er aus dem Cache.

Die Eigenheiten des Portals, die hier einmal zentral gelöst sind:
  * Semikolon als Trennzeichen
  * Komma als Dezimaltrennzeichen
  * Codes mit Präfix ("JAHR-2010", "KALW-202015", ...)
  * Klartextnamen stehen in separaten Codelisten-Dateien
"""

from __future__ import annotations

import io

import pandas as pd
import requests
import streamlit as st

BASIS = "https://data.statistik.gv.at/data/"

# Datensatz-IDs. Alle wurden gegen die Quelle geprüft.
DATENSAETZE = {
    "sterbefaelle":   "OGD_gest_kalwo_GEST_KALWOCHE_100",
    "tourismus":      "OGD_touextsai_Tour_HKL_1",
    "haeuserpreise":  "OGD_hpi2010_HPI_10_1",
    "tariflohn":      "OGD_tli16nace20_TLI_110",
    "baubewilligung": "OGD_bewwohn303_BB303_1",
    "fertilitaet":    "OGD_ind002fertilrat_HVD_FERTILRATE_1",
    "lebenserwartung": "OGD_ind003_HVD_IND_1",
    "pkw_neu":        "OGD_fkfzul0759_OD_PkwNZL_1",
}

GEOJSON_BEZIRKE = (
    "https://raw.githubusercontent.com/ginseng666/GeoJSON-TopoJSON-Austria/"
    "master/2021/simplified-99.5/bezirke_995_geo.json"
)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _lade_csv(url: str) -> pd.DataFrame:
    """Eine CSV vom Portal holen. 24 Stunden im Cache."""
    antwort = requests.get(url, timeout=90)
    antwort.raise_for_status()

    for kodierung in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(
                io.StringIO(antwort.content.decode(kodierung)),
                sep=";", decimal=",", low_memory=False,
            )
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Kodierung nicht erkannt: {url}")


def lade(schluessel: str, dimension: str | None = None) -> pd.DataFrame:
    """
    Hauptdatei oder Codeliste eines Datensatzes laden.

        lade("sterbefaelle")                  -> Hauptdatei
        lade("sterbefaelle", "C-B00-0")       -> Codeliste Bundesland
        lade("haeuserpreise", "HEADER")       -> Spaltenbeschreibung
    """
    ds = DATENSAETZE[schluessel]
    endung = f"_{dimension}" if dimension else ""
    return _lade_csv(f"{BASIS}{ds}{endung}.csv")


def codeliste(schluessel: str, dimension: str) -> pd.DataFrame:
    """Codeliste auf die zwei Spalten reduzieren, die wir brauchen."""
    df = lade(schluessel, dimension)
    return df[["code", "name"]].copy()


def ziffern(serie: pd.Series) -> pd.Series:
    """
    Zahlenteil am Ende eines Codes holen.
    "JAHR-2010" -> "2010",  "KALW-202015" -> "202015"

    Bewusst per Regex statt durch Abschneiden eines festen Präfixes:
    Statistik Austria ändert Präfixe gelegentlich, die Ziffern am Ende
    bleiben aber.
    """
    return serie.astype(str).str.extract(r"(\d+)$", expand=False)


def benenne(df: pd.DataFrame, spalte: str, schluessel: str,
            dimension: str, neu: str) -> pd.DataFrame:
    """Codespalte über die Codeliste um eine Klartextspalte ergänzen."""
    cl = codeliste(schluessel, dimension).rename(
        columns={"code": spalte, "name": neu}
    )
    return df.merge(cl, on=spalte, how="left")


def finde_code(cl: pd.DataFrame, muster: str) -> str | None:
    """
    Code suchen, dessen Name auf ein Muster passt - z.B. "insgesamt".
    Verhindert, dass wir Codes hart verdrahten, die sich ändern können.
    """
    treffer = cl[cl["name"].str.contains(muster, case=False, na=False)]
    return None if treffer.empty else treffer.iloc[0]["code"]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def lade_geojson() -> dict:
    """Bezirksgrenzen Österreichs für die Karten."""
    antwort = requests.get(GEOJSON_BEZIRKE, timeout=90)
    antwort.raise_for_status()
    geo = antwort.json()
    # Wien ist doppelt enthalten (als ein Bezirk und als 23 Gemeinde-
    # bezirke). Nur die dreistelligen Codes sind die "echten" Bezirke.
    geo["features"] = [
        f for f in geo["features"] if len(str(f["properties"]["iso"])) == 3
    ]
    return geo


# --------------------------------------------------------------------
# AUFBEREITETE DATENSÄTZE
# --------------------------------------------------------------------

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def sterbefaelle() -> pd.DataFrame:
    """Sterbefälle je Kalenderwoche, Bundesland, Altersgruppe, Geschlecht."""
    df = lade("sterbefaelle")
    df = df.rename(columns={
        "C-KALWOCHE-0": "wochencode",
        "C-B00-0": "bl_code",
        "C-ALTERGR65-0": "alter_code",
        "C-C11-0": "geschlecht_code",
        "F-ANZ-1": "tote",
    })

    z = ziffern(df["wochencode"])
    df["jahr"] = pd.to_numeric(z.str[:4], errors="coerce")
    df["woche"] = pd.to_numeric(z.str[4:6], errors="coerce")
    df["tote"] = pd.to_numeric(df["tote"], errors="coerce")
    df = df.dropna(subset=["jahr", "woche", "tote"])
    df["jahr"] = df["jahr"].astype(int)
    df["woche"] = df["woche"].astype(int)

    for sp, dim, neu in [("bl_code", "C-B00-0", "bundesland"),
                         ("alter_code", "C-ALTERGR65-0", "altersgruppe"),
                         ("geschlecht_code", "C-C11-0", "geschlecht")]:
        df = benenne(df, sp, "sterbefaelle", dim, neu)

    # Meldeverzug: die letzten Wochen des aktuellsten Jahres sind noch
    # unvollständig und würden wie ein Einbruch aussehen.
    pro_woche = df.groupby(["jahr", "woche"])["tote"].sum()
    median = pro_woche[pro_woche.index.get_level_values("jahr")
                       < df["jahr"].max()].median()
    unvollstaendig = pro_woche[(pro_woche < 0.6 * median)].index
    letztes = df["jahr"].max()
    maske = df.set_index(["jahr", "woche"]).index.isin(unvollstaendig)
    df = df[~(maske & (df["jahr"] == letztes).values)]

    return df[df["woche"].between(1, 52)]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def tourismus() -> pd.DataFrame:
    """Nächtigungen je Monat, Bundesland und Herkunftsland, ab 1973."""
    df = lade("tourismus")
    df = df.rename(columns={
        "C-SDB_TIT-0": "zeit",
        "C-W96-0": "bl_code",
        "C-C93-2": "land_code",
        "F-ANK": "ankuenfte",
        "F-UEB": "naechtigungen",
    })
    z = df["zeit"].astype(str)
    df["jahr"] = pd.to_numeric(z.str[:4], errors="coerce")
    df["monat"] = pd.to_numeric(z.str[4:6], errors="coerce")
    for sp in ("ankuenfte", "naechtigungen"):
        df[sp] = pd.to_numeric(df[sp], errors="coerce")
    df = df.dropna(subset=["jahr", "monat"])
    df["jahr"] = df["jahr"].astype(int)
    df["monat"] = df["monat"].astype(int)
    df = df[df["monat"].between(1, 12)]

    df["land_code"] = df["land_code"].astype(str)
    cl = codeliste("tourismus", "C-C93-2")
    cl["code"] = cl["code"].astype(str)
    df = df.merge(cl.rename(columns={"code": "land_code", "name": "land"}),
                  on="land_code", how="left")
    df = benenne(df, "bl_code", "tourismus", "C-W96-0", "bundesland")
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def haeuserpreise() -> pd.DataFrame:
    """Häuserpreisindex, Jahreswerte (2010 = 100)."""
    df = lade("haeuserpreise")
    z = ziffern(df["C-HPIQ-0"])
    # 4 Ziffern = Jahreswert, 5 Ziffern = Quartalswert
    jahreswerte = z.str.len() == 4
    out = pd.DataFrame({
        "jahr": pd.to_numeric(z[jahreswerte].str[:4], errors="coerce"),
        "index": pd.to_numeric(df.loc[jahreswerte, "F-HPI1"], errors="coerce"),
    }).dropna()
    out["jahr"] = out["jahr"].astype(int)
    return out.sort_values("jahr").reset_index(drop=True)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def tariflohn() -> pd.DataFrame:
    """Tariflohnindex, Jahresmittel über alle Branchen (2016 = 100)."""
    df = lade("tariflohn")
    cl_soz = codeliste("tariflohn", "C-SOZTLI-0")
    cl_nace = codeliste("tariflohn", "C-NACE20_16-0")

    code_soz = finde_code(cl_soz, "insgesamt")
    code_nace = finde_code(cl_nace, "insgesamt")

    df = df.rename(columns={
        "C-NACE20_16-0": "nace_code",
        "C-SOZTLI-0": "soz_code",
        "C-A10TLI-0": "zeit",
        "F-TLI": "index",
    })
    z = ziffern(df["zeit"])
    df["jahr"] = pd.to_numeric(z.str[:4], errors="coerce")
    df["index"] = pd.to_numeric(df["index"], errors="coerce")
    df = df.dropna(subset=["jahr", "index"])
    df["jahr"] = df["jahr"].astype(int)

    if code_soz:
        df = df[df["soz_code"] == code_soz]
    if code_nace:
        df = df[df["nace_code"] == code_nace]

    jahr = (df.groupby("jahr")
              .agg(index=("index", "mean"), monate=("index", "size"))
              .reset_index())
    return jahr[jahr["monate"] >= 12][["jahr", "index"]]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def baubewilligungen() -> pd.DataFrame:
    """Bewilligte Wohnungen je Bezirk und Jahr, ab 2010."""
    df = lade("baubewilligung")
    df = df.rename(columns={
        "C-JAHR-0": "jahrcode",
        "C-GEMOKZ-0": "region_code",
        "C-ARTBAU-0": "artbau_code",
        "C-WOHNART4-0": "wohnart_code",
        "F-ANZWOHN": "wohnungen",
    })
    df["jahr"] = pd.to_numeric(ziffern(df["jahrcode"]), errors="coerce")
    df["wohnungen"] = pd.to_numeric(df["wohnungen"], errors="coerce")
    df = df.dropna(subset=["jahr", "wohnungen"])
    df["jahr"] = df["jahr"].astype(int)

    for sp, dim, neu in [("region_code", "C-GEMOKZ-0", "region"),
                         ("artbau_code", "C-ARTBAU-0", "artbau"),
                         ("wohnart_code", "C-WOHNART4-0", "wohnart")]:
        df = benenne(df, sp, "baubewilligung", dim, neu)
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fertilitaet() -> pd.DataFrame:
    """Altersspezifische Fertilitätsrate je Alter, Region und Jahr."""
    df = lade("fertilitaet")
    df = df.rename(columns={
        "C-FERTRAT_ZEIT-0": "zeitcode",
        "C-FERTRAT_NUTS2-0": "region_code",
        "C-FERTRAT_ALTER-0": "altercode",
        "F-FERTRAT_ASFR": "rate",
    })
    df["jahr"] = pd.to_numeric(ziffern(df["zeitcode"]), errors="coerce")
    df["alter"] = pd.to_numeric(ziffern(df["altercode"]), errors="coerce")
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["jahr", "alter", "rate"])
    df[["jahr", "alter"]] = df[["jahr", "alter"]].astype(int)
    return benenne(df, "region_code", "fertilitaet",
                   "C-FERTRAT_NUTS2-0", "region")


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def lebenserwartung() -> pd.DataFrame:
    """Fernere Lebenserwartung je Alter, Geschlecht, Region und Jahr."""
    df = lade("lebenserwartung")
    df = df.rename(columns={
        "C-DEMIND_ZEIT-0": "zeitcode",
        "C-DEMIND_NUTS-0": "region_code",
        "C-DEMIND_ALTER-0": "altercode",
        "C-DEMIND_GESCHLECHT-0": "geschlecht_code",
        "F-DEMIND_LEBENSERWARTUNG-0": "restjahre",
    })
    df["jahr"] = pd.to_numeric(ziffern(df["zeitcode"]), errors="coerce")
    df["alter"] = pd.to_numeric(ziffern(df["altercode"]), errors="coerce")
    df["restjahre"] = pd.to_numeric(df["restjahre"], errors="coerce")
    df = df.dropna(subset=["jahr", "alter", "restjahre"])
    df[["jahr", "alter"]] = df[["jahr", "alter"]].astype(int)
    df = benenne(df, "geschlecht_code", "lebenserwartung",
                 "C-DEMIND_GESCHLECHT-0", "geschlecht")
    return benenne(df, "region_code", "lebenserwartung",
                   "C-DEMIND_NUTS-0", "region")


MONATE = ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun",
          "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
