import os
import json
from datetime import date, timedelta
import streamlit as st
from main import PMSOrchestrator

st.set_page_config(
    page_title="PMS & PSUR Automation Tool - MDR UE 2017/745",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    .guide-box {
        background-color: #1E293B;
        color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 14px;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 24px;
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
    st.caption("Conforme a MDR UE 2017/745, IEC 62304, IEC 62366-1 e MDCG 2019-16 | Esecuzione 100% Locale")

    config = load_config()

    # Sidebar - Gestione Competitor e Impostazioni Output
    st.sidebar.header("⚙️ Impostazioni Report")
    
    default_comp_str = ", ".join(config.get("competitors", ["O3 Enterprise", "Siemens Healthineers", "GE Healthcare"]))
    competitors_raw = st.sidebar.text_area(
        "Competitors da Evidenziare",
        value=default_comp_str,
        help="Inserisci i nomi dei fabbricanti competitor separati da virgola"
    )
    competitors_list = [c.strip() for c in competitors_raw.split(",") if c.strip()]

    output_filename = st.sidebar.text_input(
        "Nome File Excel Output",
        value=config.get("output_excel_path", "PMS_Report_MDR_2017_745.xlsx")
    )

    st.sidebar.divider()
    st.sidebar.info("""
    📌 **8 Fonti Integrate**:
    - 🇮🇹 Ministero della Salute
    - 🇺🇸 openFDA MAUDE
    - 🇺🇸 openFDA Recalls
    - 🇺🇸 FDA Safety Communications
    - 🇺🇸 FDA Letters to Health Care Providers
    - 🌐 NIST NVD Cybersecurity
    - 🇩🇪 BfArM (Germania)
    - 🇬🇧 MHRA (Regno Unito)
    """)

    tab_run, tab_audit = st.tabs(["🚀 Ricerca & Sorveglianza", "📋 Audit Log & Tracciabilità"])

    with tab_run:
        # Guida sintattica in evidenza al centro
        st.markdown("""
        <div class="guide-box">
            <b>📖 Guida per la Ricerca Regolatoria:</b><br>
            • Inserisci il nome commerciale del dispositivo (es. <code>ZEEROmed MIS</code>, <code>O3 Enterprise</code>) oppure termini clinici (es. <code>mammography</code>, <code>screening software</code>).<br>
            • Puoi cercare per parole singole o locuzioni esatte. La ricerca interrogherà contemporaneamente tutte e 6 le banche dati internazionali.
        </div>
        """, unsafe_allow_html=True)

        # BARRA DI RICERCA CENTRALE
        st.subheader("🔍 Parametri di Ricerca Principali")
        
        search_keyword = st.text_input(
            "Parola Chiave / Dispositivo Medico da analizzare:",
            value=config.get("search_keyword", "mammography"),
            placeholder="Es. mammography, screening software, ZEEROmed MIS...",
            key="main_keyword_input"
        )

        st.divider()

        # SELETTORE PERIODO TEMPORALE / CALENDARIO
        st.subheader("📅 Finestra Temporale di Sorveglianza (Filtro Date)")
        
        time_mode = st.radio(
            "Seleziona l'intervallo di pubblicazione degli avvisi:",
            ["Tutti i dati disponibili", "Ultimi 4 Mesi (PSUR SaMD)", "Ultimo Anno (12 Mesi)", "Intervallo Personalizzato (Calendario)"],
            index=0,
            horizontal=True
        )

        start_date = None
        end_date = None
        today = date.today()

        if time_mode == "Ultimi 4 Mesi (PSUR SaMD)":
            start_date = today - timedelta(days=120)
            end_date = today
            st.info(f"📆 Filtro applicato: dal **{start_date.strftime('%d/%m/%Y')}** al **{end_date.strftime('%d/%m/%Y')}**")
        elif time_mode == "Ultimo Anno (12 Mesi)":
            start_date = today - timedelta(days=365)
            end_date = today
            st.info(f"📆 Filtro applicato: dal **{start_date.strftime('%d/%m/%Y')}** al **{end_date.strftime('%d/%m/%Y')}**")
        elif time_mode == "Intervallo Personalizzato (Calendario)":
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("Data Inizio", value=today - timedelta(days=180))
            with col_d2:
                end_date = st.date_input("Data Fine", value=today)
            st.info(f"📆 Filtro personalizzato: dal **{start_date.strftime('%d/%m/%Y')}** al **{end_date.strftime('%d/%m/%Y')}**")

        st.divider()

        run_button = st.button("▶️ AVVIA SORVEGLIANZA E GENERAZIONE REPORT EXCEL")

        if run_button:
            status_box = st.status("Elaborazione pipeline in corso...", expanded=True)
            try:
                status_box.write("1️⃣ Avvio Orchestratore e configurazione filtri...")
                orchestrator = PMSOrchestrator()
                
                status_box.write("2️⃣ Interrogazione delle 6 fonti di vigilanza e cybersecurity...")
                output_file = orchestrator.run(
                    search_term=search_keyword,
                    competitors=competitors_list,
                    custom_output_path=output_filename,
                    start_date=start_date,
                    end_date=end_date
                )
                
                status_box.update(label="✅ Sorveglianza completata con successo!", state="complete", expanded=False)
                st.success(f"Report di sorveglianza salvato in: `{output_file}`")

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
                st.error(f"Si è verificato un errore: {e}")

    with tab_audit:
        st.subheader("Audit Trail & Log di Sistema (IEC 62304)")
        if os.path.exists("pms_execution.log"):
            with open("pms_execution.log", "r", encoding="utf-8") as log_file:
                log_content = log_file.read()
            st.text_area("Registro Operazioni Invariabile (pms_execution.log)", value=log_content, height=400)
        else:
            st.info("Nessun log trovato. Esegui la pipeline per generare l'Audit Trail.")


if __name__ == "__main__":
    main()
