# Tracking Avanzamento Progetto PMS Automation (MDR UE 2017/745)

- [x] Step 1: Configurazione ambiente virtuale e dipendenze
- [x] Step 2: Modulo di normalizzazione date (`core/date_normalizer.py`)
- [x] Step 3: Modulo di deduplicazione (`core/deduplicator.py`)
- [x] Step 4: Scraper Ministero della Salute (`scrapers/ministero_salute.py`)
- [x] Step 5: Scraper openFDA MAUDE (`scrapers/openfda_maude.py`)
- [x] Step 6: Tagger NLP (`core/nlp_tagger.py`)
- [x] Step 7: Generatore Excel (`core/excel_generator.py`)
- [x] Step 8: Orchestratore Principale (`main.py`) e Suite di Test Integrazione (`tests/test_main.py`)
- [x] Step 9: Configurazione Dinamica (`config.json`), caricamento Failsafe in `main.py` e suite di test estesa (`tests/test_main.py`)
- [x] Step 10: Interfaccia CLI (`argparse`), parametrizzazione completa, audit trail e suite di test completa (44 test)
- [x] Step 12: Connettori FDA Recalls (`scrapers/fda_recalls.py`), NIST NVD Cybersecurity (`scrapers/nvd_cybersecurity.py`) per SaMD MDCG 2019-16, aggiornamento `config.json` con dominio mammografia e 50 test unitari passing.
- [x] Step 13: Connettori BfArM Germania (`scrapers/bfarm.py`) e MHRA Regno Unito (`scrapers/mhra.py`), estensione orchestratore a 6 sorgenti regolatorie e 56 test unitari passing.
- [x] Step 14: Interfaccia Grafica Web Dashboard Streamlit (`app.py`), gestione interattiva 6 fonti regolatorie, audit log viewer e export Excel.
- [x] Step 15: Template protocollo DPR-385 PSUR Worksheet (`core/excel_generator.py`), connettori FDA Safety Communications (`scrapers/fda_safety_communications.py`) e FDA Letters (`scrapers/fda_letters.py`) per 8 fonti regolatorie totali, calcolo data range nel nome file e 62 test unitari passing.
- [x] Step 16: Ottimizzazione connettori openFDA MAUDE ed FDA Recalls per la gestione HTTP 404 come 0 risultati (log INFO anziché WARNING) e pulizia Audit Trail.
- [x] Step 21: Integrazione dinamica di SourceQueryFormatter nell'Orchestratore principale (`main.py`) per l'adattamento automatico di query e date su tutte le 8 banche dati regolatorie.
