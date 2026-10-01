import asyncio
import glob
import logging
import os
import re, pdfplumber
import tempfile
from pathlib import Path

import pandas as pd

from mcp_server.utils import crawler_bollettino
from mcp_server.utils.crawler_bollettino import CrawlerBollettino

ZONE = ["BAT","BA_01","BA_02","BA_03","BR_01","BR_02","FG_01","FG_02",
        "FG_03","FG_04","LE_01","LE_02","LE_03","TA_01","TA_02","TA_03"]
LIVELLI = ["BASSO", "MEDIO", "MODERATO", "ELEVATO", "ESTREMO"]
RE_LIV = re.compile(r"BAS{1,2}O|MEDIO|MODERATO|ELEVATO|ESTREMO")  # BAS{1,2}O: il dedup può fondere la doppia S
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
iso = lambda d: f"{d[6:]}-{d[3:5]}-{d[:2]}" if d else None  # gg/mm/aaaa -> aaaa-mm-gg
norm = lambda t: "BASSO" if t.startswith("BAS") else t

COLORI = {(0.0, 1.0, 0.0): "BASSO", (1.0, 1.0, 0.0): "MEDIO", (1.0, 0.75, 0.0): "MODERATO"}
CARTELLA = Path(
    os.getenv("BOLLETTINI_DIR") or Path(tempfile.gettempdir()) / "bollettini"
)
#CARTELLA.mkdir(parents=True, exist_ok=True)         # la crea se non esiste
CSV_OUT = CARTELLA / "rischio.csv"

CHIAVE = ["data_emissione", "data_previsione", "zona"]

logger = logging.getLogger(__name__)
class LoadBollettinoPdf:
    def __init__(self,bollettino_type):
        self.bollettino_type = bollettino_type
        self.pdf_path = ''

    async def get_bollettino(self) -> str | None:
        crawl = CrawlerBollettino(self.bollettino_type)
        # Run crawler: scarica i nuovi PDF
        CARTELLA.mkdir(parents=True, exist_ok=True)
        logger.info("cartella download: %s", CARTELLA)
        await asyncio.to_thread(crawl.crawl_from_last_date)
        #crawl.crawl_from_last_date()
        # Estrae i dati dai PDF (salta quelli già elaborati) e restituisce il JSON
        return self.estrai_json()

    def estrai_rischio(self):
        """
        :param :
        :return:
        Legge le tabelle "Zona Omogenea AIB / Livello Pericolosità" dei
        Bollettini regionali di previsione incendi (una tabella per ciascun giorno: 24, 48 e 72 ore) e
        produce una riga per data × zona.
        Come funziona:
        il PDF scrive ogni livello più volte sovrapposto (finto grassetto): dedupe_chars() elimina i duplicati;
        ogni livello viene assegnato alla zona in base alla posizione x della colonna nell'intestazione,
            non all'ordine del testo;
        se una tabella non ha esattamente 16 livelli, la funzione si ferma con un errore
         invece di scrivere dati sbagliati.
        """
        righe = []
        with pdfplumber.open(self.pdf_path) as pdf:
            testo_p1 = pdf.pages[0].extract_text() or ""
            m = re.search(r"Bollettino previsionale del (\d{2}/\d{2}/\d{4})", testo_p1)
            data_emissione = m.group(1) if m else None
            for page in pdf.pages:
                page = page.dedupe_chars()
                words = page.extract_words()
                for bat in [w for w in words if w["text"] == "BAT"]:
                    y = bat["top"]
                    # intestazione: posizione x di ogni zona sulla stessa riga di BAT
                    header = {w["text"]: (w["x0"] + w["x1"]) / 2 for w in words
                              if w["text"] in ZONE and abs(w["top"] - y) < 2}
                    if len(header) != 16:
                        continue  # etichetta "BAT" sulla mappa, non intestazione di tabella
                    # data della tabella: a sinistra, subito sopra l'intestazione
                    date = [w for w in words if RE_DATA.fullmatch(w["text"])
                            and w["x0"] < bat["x0"] and 0 < y - w["top"] < 40]
                    if not date:
                        raise ValueError(f"{self.pdf_path} p.{page.page_number}: data tabella non trovata")
                    data_prev = min(date, key=lambda w: y - w["top"])["text"]
                    # riga dei livelli: caratteri sotto l'intestazione, a destra dell'etichetta
                    chars = sorted((c for c in page.chars
                                    if y + 10 < c["top"] < y + 40 and c["x0"] > bat["x0"] - 10),
                                   key=lambda c: c["x0"])
                    s = "".join(c["text"] for c in chars)
                    assegnati = {}
                    for tok in RE_LIV.finditer(s):
                        cs = chars[tok.start():tok.end()]
                        xc = (cs[0]["x0"] + cs[-1]["x1"]) / 2
                        zona = min(header, key=lambda z: abs(header[z] - xc))
                        if zona in assegnati:
                            raise ValueError(f"{self.pdf_path} {data_prev}: due livelli per {zona}")
                        assegnati[zona] = tok.group()
                    if len(assegnati) != 16:
                        raise ValueError(f"{self.pdf_path} {data_prev}: {len(assegnati)} livelli su 16 ({s!r})")
                    righe += [{"data_emissione": iso(data_emissione), "data_previsione": iso(data_prev),
                               "zona": z, "livello": norm(assegnati[z]),
                               "livello_num": LIVELLI.index(norm(assegnati[z])) + 1} for z in ZONE]
        if not righe:
            raise ValueError(f"{self.pdf_path}: nessuna tabella dei livelli trovata")
        return righe

    def controlla_colori(self, righe):
        """Restituisce le discrepanze tra testo e colore della cella (lista vuota = tutto ok).
            Controllo incrociato con i colori delle celle
            Confronta il livello letto dal testo con il colore di sfondo della cella.
            I colori di BASSO, MEDIO e MODERATO sono stati verificati sul bollettino del 25/09/2026.
             Quelli di ELEVATO ed ESTREMO **non li ho ancora visti in un PDF reale**: se compaiono,
            vengono segnalati come "colore non mappato" da controllare a mano.
        """
        attesi = {(r["data_previsione"], r["zona"]): r["livello"] for r in righe}
        problemi = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                for bat in [w for w in words if w["text"] == "BAT"]:
                    y = bat["top"]
                    header = {w["text"]: (w["x0"] + w["x1"]) / 2 for w in words
                              if w["text"] in ZONE and abs(w["top"] - y) < 2}
                    if len(header) != 16:
                        continue
                    data_prev = min((w for w in words if RE_DATA.fullmatch(w["text"])
                                     and w["x0"] < bat["x0"] and 0 < y - w["top"] < 40),
                                    key=lambda w: y - w["top"])["text"]
                    data_prev = iso(data_prev)
                    celle = [r for r in page.rects if r["top"] < y + 30 < r["bottom"]
                             and r["x0"] > bat["x0"] - 10 and r["width"] < 40
                             and r["non_stroking_color"] and len(r["non_stroking_color"]) == 3
                             and tuple(round(v, 2) for v in r["non_stroking_color"]) != (0.83, 0.83,
                                                                                         0.83)]  # grigio = sfondo intestazione
                    for z, xc in header.items():
                        cella = [r for r in celle if r["x0"] <= xc <= r["x1"]]
                        if not cella:
                            problemi.append((data_prev, z, "cella colorata non trovata"))
                            continue
                        col = tuple(round(v, 2) for v in cella[0]["non_stroking_color"])
                        liv_colore = COLORI.get(col, f"colore non mappato {col}")
                        if liv_colore != attesi.get((data_prev, z)):
                            problemi.append((data_prev, z, f"testo={attesi.get((data_prev, z))} colore={liv_colore}"))
        return problemi

    def estrai_json(self) -> str | None:
        # Storico già salvato (se esiste) e PDF già elaborati
        storico = (
            pd.read_csv(CSV_OUT, dtype="string")
            if os.path.exists(CSV_OUT)
            else pd.DataFrame()
        )
        gia_letti = set(storico["file"].dropna()) if "file" in storico else set()

        nuove = []
        for path in sorted(glob.glob(os.path.join(CARTELLA, "*.pdf"))):
            self.pdf_path = path
            nome = os.path.basename(path)
            if nome in gia_letti:
                continue

            try:
                righe = self.estrai_rischio()
            except Exception as e:
                logger.warning("SALTATO %s: %s", nome, e)
                continue

            if problemi := self.controlla_colori(righe):
                logger.warning("ATTENZIONE %s: %s", nome, problemi)

            nuove.extend({**r, "file": nome} for r in righe)
            logger.info("OK %s: %d righe", nome, len(righe))

        frames = [f for f in (storico, pd.DataFrame(nuove).astype("string")) if not f.empty]
        if not frames:
            return "[]"

        df = (
            pd.concat(frames, ignore_index=True)
            .drop_duplicates(subset=CHIAVE, keep="last")
            .sort_values(CHIAVE, ignore_index=True)
        )
        df.to_csv(CSV_OUT, index=False)
        logger.info("Salvato %s: %d righe", CSV_OUT, len(df))

        return df.to_json(orient="records", force_ascii=False)