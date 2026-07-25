from datetime import datetime

SUPPORTED_FORMATS = (
    "%Y-%m-%d",  # ISO
    "%d/%m/%Y",  # Italiano / Europeo
    "%m/%d/%Y",  # Americano
    "%d.%m.%Y",  # Tedesco
)


def normalizza_data(data_str: str | None) -> str | None:
    """
    Normalizza una data in formato stringa convertendola nel formato italiano 'GG/MM/AAAA'.

    Accetta i formati:
    - ISO: YYYY-MM-DD
    - Italiano/Europeo: DD/MM/YYYY
    - Americano: MM/DD/YYYY
    - Tedesco: DD.MM.YYYY

    Restituisce None se la stringa è vuota, None o in un formato non valido/non riconosciuto.
    """
    if not data_str or not isinstance(data_str, str):
        return None

    cleaned_str = data_str.strip()
    if not cleaned_str:
        return None

    for fmt in SUPPORTED_FORMATS:
        try:
            dt = datetime.strptime(cleaned_str, fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue

    return None
