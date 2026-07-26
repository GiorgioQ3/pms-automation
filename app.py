"""
Dashboard Grafica Web Streamlit per PMS Automation Tool.
Interfaccia utente aggiornata con indicazione esplicita della regola della virgola per le keyword.
"""

import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
from main import PMSOrchestrator

st.set_page_config(
    page_title="PMS Automation Tool - SaMD (DPR-385)",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ PMS Automation & PSUR Reporting Tool")
st.caption("Conforme a MDR UE 2017/745 (Art. 83/86/88) | Protocollo DPR-385 Worksheets | IEC 62304")

# Sidebar - Configurazione e Fonti
st.sidebar.header("⚙️ Parametri di Ricerca")
preset = st.sidebar.selectbox(
    "Intervallo Temporale Preset",
    ["Personalizzato", "Ultimi 4 Mesi (PSUR Breve)", "Ultimi 12 Mesi (PSUR Annuale)"]
)

today = datetime.today()
if preset == "Ultimi 4 Mesi (PSUR Breve)":
    default_start = today - timedelta(days=120)
    default_end = today
elif preset == "Ultimi 12 Mesi (PSUR Annuale)":
    default_start = today - timedelta(days=365)
    default_end = today
else:
    default_start = today - timedelta(days=30)
    default_end = today

start_date = st.sidebar.date_input("Data Inizio Periodo", default_start)
end_date = st.sidebar.date_input("Data Fine Periodo", default_end)

st.sidebar.markdown("---")
st.sidebar.subheader("📡 Banche Dati Monitorate (8)")
st.sidebar.markdown("""
- 🇮🇹 Minister of Health
- 🇺🇸 MAUDE
- 🇺🇸 MD Recalls (FDA)
- 🇺🇸 Safety Communication (FDA)
- 🇺🇸 Letters to Health Care Providers (FDA)
- 🌐 National Vulnerability Database (NVD)
- 🇩🇪 BfArM
- 🇬🇧 MHRA
""")

# AVVISO REGOLA KEYWORDS BEN VISIBILE IN INTERFACCIA
st.warning("📌 **REGOLA FONDAMENTALE KEYWORDS**: Separa ogni parola chiave con una **virgola (`,`)**. Ciascun termine o frase separata da virgola verrà ricercato autonomamente su tutte le 8 banche dati regolatorie (es. `mammography, web based viewer, PACS`).")

search_keyword = st.text_input("🔍 Inserisci Keyword(s) per SaMD / Dispositivi Medici (separate da virgola):", "mammography, web based viewer")

if st.button("🚀 Avvia Analisi Post-Market Surveillance (DPR-385)", type="primary"):
    if not search_keyword.strip():
        st.warning("Inserisci almeno una keyword valida.")
    else:
        with st.spinner("Esecuzione ricerca indipendente per ogni keyword su tutte le 8 fonti..."):
            orchestrator = PMSOrchestrator()
            results = orchestrator.run_pipeline(
                keyword_input=search_keyword.strip(),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

        st.success(f"✅ Analisi completata! File generato: `{results['excel_filename']}`")

        # Metriche Generali e Signal Detection
        signal = results.get("signal_metrics", {})
        risk_level = signal.get("overall_risk_level", "N/A")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Keywords Cercate", len(results["keywords"]))
        col2.metric("Record Selezionati (Sel)", results["total_selected"])
        col3.metric("Eventi ad Alto Rischio / CVE", signal.get("high_severity_incidents", 0))

        if risk_level == "ALTO":
            col4.error(f"⚠️ Livello Rischio: {risk_level}")
        elif risk_level == "MEDIO":
            col4.warning(f"⚡ Livello Rischio: {risk_level}")
        else:
            col4.success(f"🟢 Livello Rischio: {risk_level}")

        # TABELLA RIASSUNTIVA FONTI CONSULTATE NELLA GUI
        st.markdown("---")
        st.subheader("🌐 Tabella Riassuntiva Fonti Consultate")
        source_summary = results.get("source_summary", [])
        if source_summary:
            df_summary = pd.DataFrame(source_summary)
            st.dataframe(df_summary, use_container_width=True)
        else:
            st.info("Nessuna informazione sulle fonti disponibile.")

        st.markdown("---")
        st.subheader("📊 Sintesi Matrice DPR-385 per Keyword")
        for kw, stats in results["keyword_stats"].items():
            with st.expander(f"🔑 Keyword: \"{kw}\""):
                st.json(stats)

        # Pulsante di Download Report Excel
        excel_path = results.get("excel_filename")
        if excel_path and os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📥 Scarica Report Excel Completo con Collegamenti Ipertestuali (Protocollo DPR-385)",
                    data=f,
                    file_name=excel_path,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# Audit Log
st.markdown("---")
with st.expander("📄 Registro di Audit Immutabile (pms_execution.log - IEC 62304)"):
    if os.path.exists("pms_execution.log"):
        with open("pms_execution.log", "r", encoding="utf-8") as log_file:
            st.code(log_file.read()[-3000:], language="log")
