import os
import json
import logging
import streamlit as st
from main import PMSOrchestrator

# Configurazione Pagina Streamlit
st.set_page_config(
    page_title="PMS & PSUR Automation Tool - MDR UE 2017/745",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS per Look & Feel Biomedico / QA-RA
st.markdown("""
    <style>
    .main-header {
        font-size: 26px;
        font-weight: bold;
        color: #1E3A8A;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)


def load_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "search_keyword": "mammography",
        "competitors": ["O3 Enterprise", "Siemens Healthineers", "GE Healthcare", "Philips"],
        "output_excel_path": "PMS_Report_MDR_2017_745.xlsx",
        "timeout_seconds": 10
    }


def main():
    st.markdown('<div class="main-header">🏥 Software di Post-Market Surveillance (PMS) & PSUR</div>', unsafe_allow_html=True)
    st.caption("Conforme a MDR UE 2017/745, IEC 62304 e MDCG 2019-16 | Esecuzione 100% Locale e Failsafe")

    config = load_config()

    # Sidebar per Parametri Operativi
    st.sidebar.header("⚙️ Configurazione Ricerca")
    
    keyword = st.sidebar.text_input(
        "Dispositivo / Parola Chiave",
        value=config.get("search_keyword", "mammography"),
        help="Inserisci il nome del dispositivo medico o keyword di ricerca (es. mammography, screening software, ZEEROmed MIS)"
    )

    default_comp_str = ", ".join(config.get("competitors", ["O3 Enterprise", "Siemens Healthineers", "GE Healthcare"]))
    competitors_raw = st.sidebar.text_area(
        "Competitors (separati da virgola)",
        value=default_comp_str,
        help="I fabbricanti inseriti qui verranno evidenziati nel report Excel"
    )
    competitors_list = [c.strip() for c in competitors_raw.split(",") if c.strip()]

    output_filename = st.sidebar.text_input(
        "Nome File Output Excel",
        value=config.get("output_excel_path", "PMS_Report_MDR_2017_745.xlsx")
    )

    st.sidebar.divider()
    st.sidebar.info("""
    📌 **6 Fonti Monitorate**:
    - 🇮🇹 Ministero della Salute
    - 🇺🇸 openFDA MAUDE (Eventi)
    - 🇺🇸 openFDA Recalls (Richiami)
    - 🌐 NIST NVD (Cybersecurity CVE)
    - 🇩🇪 BfArM (Germania - FSN)
    - 🇬🇧 MHRA (Regno Unito)
    """)

    # Area Principale - Tab
    tab_run, tab_audit = st.tabs(["🚀 Esecuzione Pipeline", "📋 Audit Log & Tracciabilità"])

    with tab_run:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Avvio Sorveglianza Proattiva")
            st.write(f"Verrà eseguita la ricerca automatizzata per la parola chiave: **'{keyword}'**")
            st.write(f"Competitor monitorati: **{len(competitors_list)}**")
            
            run_button = st.button("▶️ AVVIA PIPELINE AUTOMATIZZATA")

        if run_button:
            status_box = st.status("Esecuzione della pipeline PMS in corso...", expanded=True)
            
            try:
                status_box.write("1️⃣ Inizializzazione Orchestratore e moduli core...")
                orchestrator = PMSOrchestrator()
                
                status_box.write("2️⃣ Interrogazione simultanea delle 6 fonti regolatorie e cybersecurity...")
                output_file = orchestrator.run(
                    search_term=keyword,
                    competitors=competitors_list,
                    custom_output_path=output_filename
                )
                
                status_box.update(label="✅ Pipeline completata con successo!", state="complete", expanded=False)
                st.success(f"Report di sorveglianza generato e salvato in: `{output_file}`")

                # Bottone Download Excel
                if os.path.exists(output_file):
                    with open(output_file, "rb") as f:
                        st.download_button(
                            label="📥 SCARICA REPORT EXCEL AUDIT-READY (.XLSX)",
                            data=f,
                            file_name=os.path.basename(output_file),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            except Exception as e:
                status_box.update(label="❌ Errore durante l'esecuzione", state="error")
                st.error(f"Si è verificato un errore imprevisto: {e}")

    with tab_audit:
        st.subheader("Audit Trail & Log di Sistema (IEC 62304)")
        if os.path.exists("pms_execution.log"):
            with open("pms_execution.log", "r", encoding="utf-8") as log_file:
                log_content = log_file.read()
            st.text_area("Registro Operazioni Invariabile (pms_execution.log)", value=log_content, height=380)
        else:
            st.info("Nessun file di log trovato. Esegui la pipeline per generare l'Audit Trail.")


if __name__ == "__main__":
    main()
