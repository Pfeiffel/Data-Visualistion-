# Österreich in Daten

Interaktives Dashboard mit offenen Daten von Statistik Austria.
Gebaut mit Streamlit und Plotly.

Es liegen **keine Datendateien im Repository** – alle Datensätze werden zur
Laufzeit direkt von `data.statistik.gv.at` geladen und 24 Stunden
zwischengespeichert. Das Dashboard ist damit immer aktuell und das Repo
bleibt klein.

## Inhalt

| Seite | Inhalt |
|---|---|
| **Sterblichkeit** | Wöchentliche Sterbefälle seit 2000. Saisonalität, Übersterblichkeit, Alt gegen Jung |
| **Wohnen** | Häuserpreise gegen Löhne, Baubewilligungen je Bezirk (Schwerpunkt Oberösterreich) |
| **Tourismus** | Nächtigungen seit 1973. Winter- gegen Sommerland, Herkunftsländer |
| **Demografie** | Fertilität nach Alter der Mutter, Lebenserwartung |

Jede Seite ist interaktiv: Filter für Zeitraum, Region und Kategorie,
umschaltbare Darstellungen (absolut / relativ / Abweichung), Tooltips auf
allen Grafiken und CSV-Download der gefilterten Daten.

## Lokal starten

```bash
git clone <DEIN-REPO-URL>
cd at-daten-dashboard

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Die App öffnet sich auf `http://localhost:8501`.

Der **erste Aufruf jeder Seite dauert einige Sekunden**, weil die Daten
heruntergeladen werden. Danach kommen sie aus dem Cache.

## Online stellen (kostenlos)

Das Repo ist für **Streamlit Community Cloud** vorbereitet:

1. Repository auf GitHub pushen (öffentlich)
2. Auf [share.streamlit.io](https://share.streamlit.io) mit GitHub anmelden
3. *New app* → Repository wählen → Main file: `app.py` → *Deploy*

Mehr ist nicht nötig – `requirements.txt` und `.streamlit/config.toml`
werden automatisch erkannt. Du bekommst eine öffentliche URL.

## Aufbau

```
at-daten-dashboard/
├── app.py                    Startseite
├── requirements.txt
├── .streamlit/config.toml    Farbthema
├── src/
│   ├── data.py               Datenzugriff + Zwischenspeicher
│   └── theme.py              Farben und Plotly-Layout
└── pages/
    ├── 1_Sterblichkeit.py
    ├── 2_Wohnen.py
    ├── 3_Tourismus.py
    └── 4_Demografie.py
```

Streamlit erkennt den Ordner `pages/` automatisch und baut daraus die
Navigation. Die Zahl am Dateianfang bestimmt die Reihenfolge.

## Eine neue Seite hinzufügen

1. Datei `pages/5_MeinThema.py` anlegen
2. Datensatz-ID in `src/data.py` unter `DATENSAETZE` eintragen
3. Lade- und Aufbereitungsfunktion daneben schreiben (die bestehenden sind
   die Vorlage)
4. Auf der Seite `from src import data as d` und `from src.theme import style`
   verwenden – damit sieht die neue Grafik automatisch aus wie alle anderen

## Worauf beim Datenportal zu achten ist

Diese Eigenheiten sind in `src/data.py` einmal zentral gelöst – wer eigene
Datensätze ergänzt, stolpert sonst darüber:

- **Semikolon** als Spaltentrennzeichen, **Komma** als Dezimaltrennzeichen.
  Ohne `decimal=","` liest pandas Zahlen als Text ein.
- Codes tragen **Präfixe** (`JAHR-2010`, `KALW-202015`). Diese Präfixe ändert
  Statistik Austria gelegentlich, die Ziffern am Ende bleiben – deshalb
  werden sie per Regex geholt und nicht durch Abschneiden fester Längen.
- Klartextnamen stehen in **separaten Codelisten-Dateien**
  (`..._C-DIMENSION.csv`). Codes nie hart verdrahten, sondern über die
  Codeliste auflösen.
- Beim Datensatz zu Baubewilligungen heißt die Regionenspalte zwar
  `C-GEMOKZ-0`, enthält aber **Bezirks-Ordnungszahlen**, keine
  Gemeindekennziffern. Die Zuordnung läuft dort über Namen.
- Aktuelle Zeiträume sind oft **unvollständig** (Meldeverzug bei
  Sterbefällen, laufendes Jahr bei Jahresdaten). Die Ladefunktionen
  schneiden solche Werte ab, damit keine falschen Einbrüche entstehen.

## Datenquelle und Lizenz

Daten: **Statistik Austria** – [data.statistik.gv.at](https://data.statistik.gv.at),
lizenziert unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de).
Bei Weiterverwendung ist die Quelle anzugeben.

Kartengrundlage: [GeoJSON-TopoJSON-Austria](https://github.com/ginseng666/GeoJSON-TopoJSON-Austria).
