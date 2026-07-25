import time
import httpx


def controlla_con_retry(
    url: str, tentativi: int = 3, attesa_secondi: float | int = 2, timeout: int = 30
) -> bool:
    """
    Esegue un health check HTTP GET su un URL specificato con logica di retry.

    Restituisce True se il server è raggiungibile e risponde con uno status code < 500.
    Se si verificano eccezioni di rete o risposte con status code >= 500,
    attende `attesa_secondi` e riprova fino al numero massimo di `tentativi`.
    Restituisce False se tutti i tentativi falliscono, senza sollevare eccezioni.
    """
    if not url or not isinstance(url, str):
        return False

    for tentativo in range(1, tentativi + 1):
        try:
            response = httpx.get(url, timeout=timeout)
            if response.status_code < 500:
                return True
        except (httpx.RequestError, httpx.HTTPError, Exception):
            pass

        if tentativo < tentativi and attesa_secondi > 0:
            time.sleep(attesa_secondi)

    return False
