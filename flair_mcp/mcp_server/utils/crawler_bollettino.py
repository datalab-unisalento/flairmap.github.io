import logging
import os
import tempfile
import time
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from mcp_server.utils.constants import SITE_CONFIG, MESI_IT

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, unquote

DEFAULT_DOWNLOAD_DIR = os.getenv(
    "BOLLETTINI_DIR", os.path.join(tempfile.gettempdir(), "bollettini")
)


logger = logging.getLogger(__name__)
class CrawlerBollettino:

    def __init__(self,site_key):
        self.SITE_CONFIG = SITE_CONFIG
        self.site_key = site_key
        self.config = self.get_config(site_key)
        self.driver = self.init_driver()

    #SETUP selenium

    def get_config(self,site_key):
        """Recupera la configurazione per un sito specifico"""
        logger.info(f"site_key: {site_key}")
        return self.SITE_CONFIG[site_key]

    def init_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        host = os.getenv('SELENIUM_HOST', 'selenium-flair')
        port = os.getenv('SELENIUM_PORT', '4444')

        return webdriver.Remote(
            command_executor=f'http://{host}:{port}',
            options=options,
        )

    def handle_popup(self):
        try:
            # Click the checkboxes
            policy = self.driver.find_element(By.XPATH, "//span[@id='spanCB1']")
            policy.click()

            policy2 = self.driver.find_element(By.XPATH, "//span[@id='spanCB2']")
            policy2.click()

            # Click the button to show more options
            policy3 = self.driver.find_element(By.XPATH, "//button[@type='button']")
            policy3.click()
            # close_pop_up = driver.find_element(*popup_selector)
            # driver.execute_script("arguments[0].click();", close_pop_up)
            logger.info("popup button closed: OK")
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
            logger.error("Unable to close popup button: KO")
        except Exception as e:
            logger.error(f"An unknown error occurred: KO ->  {e}")

    def data_oggi_ita(self, oggi=None):
        oggi = oggi or datetime.now()
        return f"{oggi.day} {MESI_IT[oggi.month - 1]} {oggi.year}"

    # SETUP PDF
    def scarica_pdf(self, href, cartella=None, nome_file=None):
        cartella = cartella or DEFAULT_DOWNLOAD_DIR
        logger.info("cartella=%r nome_file=%r", cartella, nome_file)
        os.makedirs(cartella, exist_ok=True)

        if nome_file is None:
            oggi_str = self.data_oggi_ita().replace(" ", "_")
            nome_file = f"bollettino_{oggi_str}.pdf"

        percorso_completo = os.path.join(cartella, nome_file)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        r = requests.get(href, headers=headers, timeout=30)
        r.raise_for_status()  # solleva errore se status != 200
        if not r.content.startswith(b'%PDF'):
            raise ValueError(f"Il link non restituisce un PDF (Content-Type: {r.headers.get('Content-Type')}): {href}")

        with open(percorso_completo, 'wb') as f:
            f.write(r.content)

        logger.info(f"PDF salvato in: {percorso_completo}")
        return percorso_completo

    def nome_file_da_url(self,href, fallback):
        """Nome originale del PDF preso dal link (es. 20260925_106_BollettinoIncendi_784.pdf).
        Nei link del portale il nome è un segmento intermedio: /documents/.../NOME.pdf/<uuid>?t=..."""
        segmenti = [unquote(s) for s in urlparse(href).path.split('/') if s.lower().endswith('.pdf')]
        return segmenti[-1] if segmenti else fallback

    def crawl_from_last_date(self, cartella: str = DEFAULT_DOWNLOAD_DIR):
        """Scarica tutti i bollettini pubblicati oggi sulla pagina di `site_key`. Restituisce i percorsi salvati."""
        config = self.get_config(self.site_key)
        url = config['selectors']['url']
        today = self.data_oggi_ita()
        scaricati = []

        driver = self.init_driver()
        try:
            logger.info(f'url bollettino: {url}')
            driver.get(url)
            # la lista dei risultati viene caricata dopo la pagina: aspetta che compaia
            container = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(config['selectors']['list_block']))
            block_list = container.find_elements(By.XPATH, "./*")  # tutti i figli diretti
            logger.info("Iterating through block of length:", len(block_list))

            for block in block_list:
                try:
                    data_text = block.find_element(By.CLASS_NAME, "data-news").text.strip()
                except NoSuchElementException:
                    continue  # blocco senza data (es. separatori)
                logger.info(f"Confronto: '{data_text}' vs '{today}'")
                if data_text != today:
                    continue
                href = block.find_element(By.TAG_NAME, "a").get_attribute("href")
                nome = self.nome_file_da_url(href, fallback=f"{self.site_key}_{today.replace(' ', '_')}.pdf")
                logger.info(f"Trovata card di oggi: {block.text!r}\n  Link: {href}")
                scaricati.append(self.scarica_pdf(href, cartella, nome))
                time.sleep(config['wait_time'])
            return scaricati
        except TimeoutException:
            logger.info(f"Lista dei bollettini non trovata su {url}: la pagina potrebbe avere una struttura diversa")
        finally:
            driver.quit()