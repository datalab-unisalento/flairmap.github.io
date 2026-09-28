from selenium.webdriver.common.by import By


SITE_CONFIG = {
        'bollettino_puglia': {
            'selectors': {
                'url': 'https://protezionecivile.regione.puglia.it/bollettino-di-criticit%C3%A0',
                'list_block': (By.CLASS_NAME, "lista-servizi-ricerca"),
                'block_name': (By.CLASS_NAME, 'card-servizio'),
                'cookie_button': (By.CLASS_NAME, 'c-bn'),
                'close_pop_up': (By.ID, 'close-pop-up-button'),
                # 'page_element': (By.CLASS_NAME, 'toolbar-number'),
                # 'href_link': (By.CLASS_NAME, 'product-item-link'),

            },
            'wait_time': 2,
            'pagination_param': 'p',
            'query_cat': 'q'
        },
        'bollettino_incendi': {
            # stessa struttura della pagina di criticità (stesso modulo "Cerca tra i Bollettini")
            'selectors': {
                'url': 'https://protezionecivile.regione.puglia.it/bollettini-incendi-boschivi',
                'list_block': (By.CLASS_NAME, "lista-servizi-ricerca"),
                'block_name': (By.CLASS_NAME, 'card-servizio'),
                'cookie_button': (By.CLASS_NAME, 'c-bn'),
                'close_pop_up': (By.ID, 'close-pop-up-button'),
            },
            'wait_time': 2,
            'pagination_param': 'p',
            'query_cat': 'q'
        }
    }



MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
               "agosto", "settembre", "ottobre", "novembre", "dicembre"]


