# Datasets

La cartella `datasets` contiene i dataset utilizzati dal progetto, insieme ai dati storici e ai file ottenuti tramite procedure di estrazione automatica.

## `rischi.csv`

File `.csv` estratto dal **Bollettino di previsione del rischio incendi del 25 settembre**, tramite il notebook:

```text
notebook/03-crawler...
```

Il dataset contiene i dati relativi al rischio estratti dal bollettino.

## `firms_puglia.csv`

File `.csv contenente i **focolai attivi rilevati in Puglia**, scaricato il **25 settembre** tramite il notebook:

```text
notebook/05-...
```

Il dataset viene ottenuto utilizzando le **API NASA FIRMS**.

### Aggiornamento dei focolai attivi

I dati relativi ai focolai attivi utilizzati nella pagina:

```text
focolai.html
```

vengono aggiornati **automaticamente ogni 30 minuti**.

L'aggiornamento viene effettuato tramite uno script Python presente nella cartella:

```text
scripts/
```

Lo script interroga periodicamente le API NASA FIRMS e aggiorna i dati utilizzati dalla pagina.

## `incendi_meteo_dir_zone.csv`

Dataset **storico** nel quale, per ogni comune, sono stati associati i relativi **codici delle zone AIB**.

Il dataset è attualmente **non utilizzato da `index.html`**, ma viene mantenuto nel progetto come riferimento storico.
