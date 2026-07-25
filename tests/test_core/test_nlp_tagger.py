import pytest
from core.nlp_tagger import assegna_tag


def test_cybersecurity_it():
    assert (
        assegna_tag("Rilevata una vulnerabilità di sicurezza informatica.")
        == "Cybersecurity"
    )
    assert assegna_tag("Richiesta patch per minaccia malware.") == "Cybersecurity"
    assert (
        assegna_tag("Attacco ransomware identificato nel sistema.")
        == "Cybersecurity"
    )


def test_cybersecurity_en():
    assert (
        assegna_tag("A critical CVE-2024-1234 vulnerability was detected.")
        == "Cybersecurity"
    )
    assert (
        assegna_tag("Cybersecurity alert regarding system breach.")
        == "Cybersecurity"
    )


def test_cybersecurity_de():
    assert (
        assegna_tag("Eine kritische Schwachstelle wurde behoben.")
        == "Cybersecurity"
    )


def test_interfaccia_grafica_it():
    assert (
        assegna_tag("Errore nel layout dell'interfaccia grafica.")
        == "Interfaccia/Grafica"
    )
    assert (
        assegna_tag("Anomalia nel display del dispositivo medico.")
        == "Interfaccia/Grafica"
    )


def test_interfaccia_grafica_en():
    assert (
        assegna_tag("Issue with the user interface display.") == "Interfaccia/Grafica"
    )
    assert assegna_tag("Flickering screen on the UI.") == "Interfaccia/Grafica"


def test_interfaccia_grafica_de():
    assert (
        assegna_tag("Fehler in der Benutzeroberfläche des Geräts.")
        == "Interfaccia/Grafica"
    )


def test_integrita_dati_it():
    assert (
        assegna_tag("Rischio di integrità dati durante l'esportazione.")
        == "Integrità Dati"
    )
    assert (
        assegna_tag("Possibile corruzione dati nel database.") == "Integrità Dati"
    )


def test_integrita_dati_en():
    assert (
        assegna_tag("Potential data loss during system shutdown.")
        == "Integrità Dati"
    )
    assert (
        assegna_tag("Data integrity check failed on restart.") == "Integrità Dati"
    )


def test_integrita_dati_de():
    assert (
        assegna_tag("Warnung bezüglich der Datenintegrität.") == "Integrità Dati"
    )


def test_priorita_match():
    # Cybersecurity ha priorità su Interfaccia/Grafica e Integrità Dati
    assert (
        assegna_tag("Vulnerabilità nell'interfaccia utente del display.")
        == "Cybersecurity"
    )
    assert (
        assegna_tag("CVE-2024-9999 che comporta corruzione dati.")
        == "Cybersecurity"
    )
    # Interfaccia/Grafica ha priorità su Integrità Dati
    assert (
        assegna_tag("Problema nell'interfaccia utente che causa data loss.")
        == "Interfaccia/Grafica"
    )


def test_fallback_generico():
    assert (
        assegna_tag("Manutenzione ordinaria del software di supporto.")
        == "Generico"
    )
    assert assegna_tag("") == "Generico"
    assert assegna_tag("   ") == "Generico"
    assert assegna_tag(None) == "Generico"
    assert assegna_tag(12345) == "Generico"
