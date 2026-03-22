import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
import numpy as np

st.set_page_config(layout="wide")
st.title("⚡Agent Wise Reports")

# Main tabs
tab1, tab2 = st.tabs(["📊 Agent Reports", "🎯 PC Hit Report"])

TEAM_URL = "https://docs.google.com/spreadsheets/d/1hrPKsQu2_dpB4wqY-Cacym47tc6ajVJa/gviz/tq?tqx=out:csv"
TARGET_URL = "https://docs.google.com/spreadsheets/d/1hUhpUGf35nYdcyoeU1jwArhkHhxFWuPJmNrKgLxv_IA/gviz/tq?tqx=out:csv"

def format_indian(num):
    try:
        num = int(num)
        s = str(num)
        if len(s) <= 3:
            return s
        last3 = s[-3:]
        rest = s[:-3]
        rest = ",".join([rest[max(i-2,0):i] for i in range(len(rest), 0, -2)][::-1])
        return rest + "," + last3
    except:
        return num

@st.cache_data
def load_team():
    df = pd.read_csv(TEAM_URL)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Emp ID": "EMP ID", "UP-TL": "TL"})
    df["EMP ID"] = df["EMP ID"].astype(str).str.strip().str.zfill(5)  # zero‑padded for agent reports
    return df

@st.cache_data
def load_team_raw():
    """Load team data without zero‑padding (for PC Hit Report)."""
    df = pd.read_csv(TEAM_URL)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Emp ID": "EMP ID", "UP-TL": "TL"})
    df["EMP ID"] = df["EMP ID"].astype(str).str.strip()  # keep original alphanumeric
    return df

@st.cache_data
def load_targets():
    df = pd.read_csv(TARGET_URL)
    df.columns = df.columns.str.strip()
    df["Target"] = pd.to_numeric(df["Target"], errors="coerce").fillna(0)
    return df

team_df = load_team()
target_df = load_targets()

# Agent Reports Tab (unchanged – your existing perfect code)
with tab1:
    process_map = {
        "Airtel_New": "Airtel_new",
        "Airtel": "Airtel_new",
        "Repeat SA": "SA_Repeat",
        "Repeat FPLP": "FPLP_Repeat",
        "Repeat FPL": "FPL_Repeat",
        "PLSE": "PLSE_Upmint",
        "Phone Pay": "Phonepe_New",
        "Super Money": "SuperMoney",
        "Money control": "Moneycontrol_new",
        "PayTM Business": "Paytm_New_BL",
        "PayTM Personal": "Paytm_New",
        "Paytm Business": "Paytm_New_BL",
        "Paytm Personal": "Paytm_New",
        "PhonePe": "Phonepe_New",
        "Phonepe": "Phonepe_New"
    }

    new_processes = ["Airtel", "Airtel_New", "Phone Pay",
                    "Super Money", "Money control", "Paytm_New",
                    "Paytm_New_BL", "Phonepe_New", "Moneycontrol_new",
                    "PayTM Personal", "PayTM Business", "Paytm Personal", "Paytm Business",
                    "PhonePe", "Phonepe"]

    @st.cache_data
    def load_sales(file):
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        df["campaignId"] = pd.to_numeric(df["campaignId"], errors="coerce")
        df.loc[df["campaignId"] == 36, "Process_Name"] = "Airtel_New"
        df["agentid"] = df["agentid"].astype(str).str.strip()
        df["Dialed_Date"] = pd.to_datetime(df["Dialed_Date"], errors="coerce")
        df["principaldue"] = pd.to_numeric(df["principaldue"], errors="coerce").fillna(0)
        df["loan_status"] = df["loan_status"].astype(str).str.lower().str.strip()
        return df

    sales_file = st.file_uploader("Upload Sales File", type=["xlsx", "csv"])

    if sales_file:
        sales_df = load_sales(sales_file)

        st.sidebar.header("Filters")
        selected_tl = st.sidebar.selectbox("Select TL", sorted(team_df["TL"].dropna().unique()))
        team_filtered = team_df[team_df["TL"] == selected_tl]

        selected_process = st.sidebar.selectbox(
            "Select Process",
            sorted(team_filtered["Process"].dropna().unique())
        )

        selected_date = st.sidebar.date_input("Select Date")
        report_type = st.sidebar.radio(
            "Select Report Type",
            ["Yesterday Overall", "Hourly Report"]
        )
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        report_time_text = f"📅 Yesterday Overall ({selected_date})" if report_type == "Yesterday Overall" else f"⏱️ {current_time.strftime('%I %p')} Report"

        df_sales = sales_df[
            (sales_df["Dialed_Date"].dt.date == selected_date) &
            (sales_df["loan_status"] == "same_day")
        ]
        df_sales = df_sales[df_sales["Process_Name"] != "Gama_New"]

        # Lookup Logic
        st.sidebar.header("Lookup Options")
        usid_input = st.sidebar.text_input("Enter Agent ID (USID)")
        if usid_input:
            data = df_sales[df_sales["agentid"] == usid_input]
            if not data.empty:
                st.subheader(f"🔎 Data for Agent ID: {usid_input}")
                st.dataframe(data)
            else:
                st.warning("No data found for this Agent ID")

        kbuserid_input = st.sidebar.text_input("Enter KBUSERID")
        if kbuserid_input:
            if "kbuserid" in df_sales.columns:
                df_sales["kbuserid"] = df_sales["kbuserid"].astype(str)
                data = df_sales[df_sales["kbuserid"] == kbuserid_input]
                if not data.empty:
                    st.subheader(f"🔎 Data for KBUSERID: {kbuserid_input}")
                    st.dataframe(data)
                else:
                    st.warning("No data found for this KBUSERID")
            else:
                st.warning("kbuserid column not present in file")

        # MAIN REPORT LOGIC
        base_agents = team_filtered[team_filtered["Process"] == selected_process][
            ["EMP ID", "Name", "Process", "TL"]
        ].copy()

        df = base_agents.merge(df_sales, left_on="EMP ID", right_on="agentid", how="left")
        df["Process_Target"] = df["Process"].map(process_map)
        df = df.merge(target_df, on=["TL", "Process_Target"], how="left")

        df["principaldue"] = df["principaldue"].fillna(0)
        df["Target"] = df["Target"].fillna(0)

        is_new = selected_process in new_processes

        if is_new:
            report = df.groupby(
                ["EMP ID", "Name", "Process", "TL", "Target"], as_index=False
            ).agg({"agentid": "count"}).rename(columns={"agentid": "Count"})
            
            all_agents_report = base_agents.merge(
                report, on=["EMP ID", "Name", "Process", "TL"], how="left"
            )
            all_agents_report["Count"] = all_agents_report["Count"].fillna(0).astype(int)
            all_agents_report["Target"] = all_agents_report["Target"].fillna(0)
            
            all_agents_report["Remaining"] = all_agents_report["Target"] - all_agents_report["Count"]
            all_agents_report["% Achieved"] = (
                (all_agents_report["Count"] / all_agents_report["Target"] * 100)
                .replace([float('inf'), -float('inf')], 0)
                .fillna(0).round(0).astype(int)
            )
            
            report = all_agents_report.sort_values(by="Count", ascending=False)
            total_value = report["Count"].sum()
            value_col = "Count"

        else:
            report = df.groupby(
                ["EMP ID", "Name", "Process", "TL", "Target"], as_index=False
            ).agg({"principaldue": "sum"}).rename(columns={"principaldue": "GMV"})
            
            all_agents_report = base_agents.merge(
                report, on=["EMP ID", "Name", "Process", "TL"], how="left"
            )
            all_agents_report["GMV"] = all_agents_report["GMV"].fillna(0)
            all_agents_report["Target"] = all_agents_report["Target"].fillna(0)
            
            all_agents_report["Remaining"] = all_agents_report["Target"] - all_agents_report["GMV"]
            all_agents_report["% Achieved"] = (
                (all_agents_report["GMV"] / all_agents_report["Target"] * 100)
                .replace([float('inf'), -float('inf')], 0)
                .fillna(0).round(0).astype(int)
            )
            
            report = all_agents_report.sort_values(by="GMV", ascending=False)
            total_value = report["GMV"].sum()
            value_col = "GMV"

        total_target = report["Target"].sum()
        total_remaining = total_target - total_value
        total_percent = int((total_value / total_target) * 100) if total_target else 0

        total_row = pd.DataFrame([{
            "EMP ID": "",
            "Name": "TOTAL",
            "Process": "",
            "TL": selected_tl,
            "Target": total_target,
            value_col: total_value,
            "Remaining": total_remaining,
            "% Achieved": total_percent
        }])

        report = pd.concat([report, total_row], ignore_index=True)

        if is_new:
            report = report[["EMP ID", "Name", "Process", "TL", "Target", "Count", "Remaining", "% Achieved"]]
        else:
            report = report[["EMP ID", "Name", "Process", "TL", "Target", "GMV", "Remaining", "% Achieved"]]

        display_df = report.copy()

        if is_new:
            display_df["Count"] = display_df["Count"].fillna(0).astype(int)
        else:
            display_df["GMV"] = display_df["GMV"].apply(format_indian)

        display_df["Target"] = display_df["Target"].apply(format_indian)
        display_df["Remaining"] = display_df["Remaining"].apply(format_indian)
        display_df["% Achieved"] = display_df["% Achieved"].astype(str) + "%"
        display_df = display_df.astype(str)
        st.subheader(f"📋 {selected_tl} | {selected_process} | {report_time_text}")
        st.dataframe(display_df)

        # IMAGE EXPORT
        rows = len(display_df)
        fig, ax = plt.subplots(figsize=(30, rows * 1.2 + 3))
        ax.axis('off')

        table = ax.table(
            cellText=display_df.values,
            colLabels=display_df.columns,
            cellLoc='center',
            loc='center'
        )

        table.auto_set_font_size(False)
        table.set_fontsize(16)
        table.scale(1.6, 2.2)

        n_rows = len(display_df)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color='white', weight='bold')
            elif row == n_rows:
                cell.set_facecolor("#D9D9D9")
                cell.set_text_props(weight='bold')
            else:
                cell.set_facecolor("#FFFFFF")

            cell.set_edgecolor("#000000")
            cell.set_linewidth(0.7)

        percent_col = list(display_df.columns).index("% Achieved")

        for i in range(1, n_rows):
            val = report.iloc[i-1]["% Achieved"]
            cell = table[(i, percent_col)]

            if val >= 100:
                cell.set_facecolor('#C6EFCE')
            elif val >= 70:
                cell.set_facecolor('#FFEB9C')
            else:
                cell.set_facecolor('#FFC7CE')

        plt.tight_layout()
        plt.savefig("report.png", dpi=200, bbox_inches='tight')

        st.image("report.png", caption="📸 Ultra Clear WhatsApp Ready")

        with open("report.png", "rb") as f:
            st.download_button("⬇ Download Image", f, "report.png")

    else:
        st.warning("⚠️ Upload a file to continue")

# ✅ PC Hit Report Tab (FIXED)
with tab2:
    st.header("🎯 PC Hit Report")
    
    pc_file = st.file_uploader("Upload Telecalling Disbursal Dump", type=["xlsx", "csv"], key="pc_file")
    
    if pc_file:
        @st.cache_data
        def load_pc_data(file):
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            df.columns = df.columns.str.strip()
            df["dial_dt"] = pd.to_datetime(df["dial_dt"], errors="coerce")
            df["agentid"] = df["agentid"].astype(str).str.strip()
            return df
        
        pc_df = load_pc_data(pc_file)
        team_raw = load_team_raw()
        
        st.sidebar.header("PC Hit Filters")
        
        gamma_tls = sorted(team_raw[team_raw["Process"] == "Gamma"]["TL"].dropna().unique())
        selected_gamma_tl = st.sidebar.selectbox("Select Gamma TL", gamma_tls)
        selected_pc_date = st.sidebar.date_input("Select PC Hit Date")
        
        pc_report_type = st.sidebar.radio(
            "PC Report Type",
            ["Yesterday Overall", "Hourly Report"]
        )
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        pc_time_text = f"📅 Yesterday Overall ({selected_pc_date})" if pc_report_type == "Yesterday Overall" else f"⏱️ {current_time.strftime('%I %p')} Report"
        
        # Debug expander (optional)
        st.sidebar.markdown("---")
        with st.sidebar.expander("🔍 Debug Info (PC Hit)", expanded=False):
            st.write(f"Total rows: {len(pc_df)}")
            st.write(f"Rows on selected date {selected_pc_date}: {len(pc_df[pc_df['dial_dt'].dt.date == selected_pc_date])}")
            st.write("Sample agentids (PC):", pc_df["agentid"].dropna().head().tolist())
            if "talktime" in pc_df.columns:
                st.write("Talktime values:", pc_df["talktime"].dropna().unique()[:10])
            if "high_talktime" in pc_df.columns:
                st.write("High talktime values:", pc_df["high_talktime"].dropna().unique()[:10])
            if "post_pc_hit" in pc_df.columns:
                st.write("Post PC hit non‑empty:", pc_df["post_pc_hit"].notna().sum())
        
        # Robust filtering
        date_mask = pc_df["dial_dt"].dt.date == selected_pc_date
        
        if "talktime" in pc_df.columns:
            if pd.api.types.is_numeric_dtype(pc_df["talktime"]):
                talktime_mask = pc_df["talktime"] > 30
            else:
                talktime_mask = pc_df["talktime"].astype(str).str.contains(">30", case=False, na=False)
        else:
            talktime_mask = True
        
        if "high_talktime" in pc_df.columns:
            if pd.api.types.is_numeric_dtype(pc_df["high_talktime"]):
                high_talktime_mask = pc_df["high_talktime"] >= 30
            else:
                high_talktime_mask = pc_df["high_talktime"].astype(str).str.contains(">=30", case=False, na=False)
        else:
            high_talktime_mask = True
        
        if "post_pc_hit" in pc_df.columns:
            post_pc_hit_mask = pc_df["post_pc_hit"].notna() & (pc_df["post_pc_hit"].astype(str).str.strip() != "")
        else:
            post_pc_hit_mask = True
        
        pc_filtered = pc_df[date_mask & talktime_mask & high_talktime_mask & post_pc_hit_mask].copy()
        
        st.sidebar.write(f"✅ PC Hits found after filters: **{len(pc_filtered)}**")
        if len(pc_filtered) > 0:
            st.sidebar.write("Sample agentids (filtered):", pc_filtered["agentid"].head().tolist())
        
        gamma_agents = team_raw[
            (team_raw["TL"] == selected_gamma_tl) & 
            (team_raw["Process"] == "Gamma")
        ][["EMP ID", "Name", "Process", "TL"]].copy()
        
        # Merge
        pc_hits_count = pc_filtered.groupby("agentid").size().reset_index(name="Achieved")
        pc_merged = gamma_agents.merge(
            pc_hits_count,
            left_on="EMP ID", 
            right_on="agentid", 
            how="left"
        )
        
        gamma_target_row = target_df[
            (target_df["TL"] == selected_gamma_tl) & 
            (target_df["Process_Target"] == "Gamma")
        ]
        gamma_target = gamma_target_row["Target"].iloc[0] if not gamma_target_row.empty else 21
        
        pc_merged["Target"] = gamma_target
        pc_merged["Achieved"] = pc_merged["Achieved"].fillna(0).astype(int)
        pc_merged["Remaining"] = pc_merged["Target"] - pc_merged["Achieved"]
        pc_merged["% Achieved"] = (
            (pc_merged["Achieved"] / pc_merged["Target"] * 100)
            .replace([float('inf'), -float('inf')], 0)
            .fillna(0).round(0).astype(int)
        )
        
        total_target_pc = pc_merged["Target"].sum()
        total_achieved_pc = pc_merged["Achieved"].sum()
        total_remaining_pc = total_target_pc - total_achieved_pc
        total_percent_pc = int((total_achieved_pc / total_target_pc * 100)) if total_target_pc else 0
        
        total_row_pc = pd.DataFrame([{
            "EMP ID": "",
            "Name": "TOTAL",
            "Process": "",
            "TL": selected_gamma_tl,
            "Target": total_target_pc,
            "Achieved": total_achieved_pc,
            "Remaining": total_remaining_pc,
            "% Achieved": total_percent_pc
        }])
        
        # ----- NEW: Sort agents by % Achieved descending (highest first) -----
        pc_agents_sorted = pc_merged[["EMP ID", "Name", "Process", "TL", "Target", "Achieved", "Remaining", "% Achieved"]].sort_values(by="% Achieved", ascending=False)
        final_pc_report = pd.concat([pc_agents_sorted, total_row_pc], ignore_index=True)
        
        # Format display (unchanged)
        final_pc_display = final_pc_report.copy()
        final_pc_display["Target"] = final_pc_display["Target"].apply(format_indian)
        final_pc_display["Achieved"] = final_pc_display["Achieved"].astype(int)
        final_pc_display["Remaining"] = final_pc_display["Remaining"].apply(format_indian)
        final_pc_display["% Achieved"] = final_pc_display["% Achieved"].astype(str) + "%"
        final_pc_display = final_pc_display.astype(str)  # ← ADD THIS LINE
        st.subheader(f"🎯 PC Hit Report | {selected_gamma_tl} | Gamma | {pc_time_text}")
        st.dataframe(final_pc_display)
        
        # Image export (unchanged, uses sorted final_pc_report)
        rows_pc = len(final_pc_display)
        fig_pc, ax_pc = plt.subplots(figsize=(25, rows_pc * 1.2 + 3))
        ax_pc.axis('off')

        table_pc = ax_pc.table(
            cellText=final_pc_display.values,
            colLabels=final_pc_display.columns,
            cellLoc='center',
            loc='center'
        )

        table_pc.auto_set_font_size(False)
        table_pc.set_fontsize(14)
        table_pc.scale(1.6, 2.2)

        n_rows_pc = len(final_pc_display)

        for (row, col), cell in table_pc.get_celld().items():
            if row == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color='white', weight='bold')
            elif row == n_rows_pc:
                cell.set_facecolor("#D9D9D9")
                cell.set_text_props(weight='bold')
            else:
                cell.set_facecolor("#FFFFFF")
            cell.set_edgecolor("#000000")
            cell.set_linewidth(0.7)

        percent_col_pc = list(final_pc_display.columns).index("% Achieved")

        achieved_col = final_pc_report["% Achieved"]
        threshold_high = np.percentile(achieved_col, 70)  # e.g., 84.3% in sample data
        threshold_med = np.percentile(achieved_col, 40)   # e.g., 64.0% in sample data
        for i in range(1, n_rows_pc):
            val = final_pc_report.iloc[i-1]["% Achieved"]
            cell = table_pc[(i, percent_col_pc)]

            if val >= threshold_high:
                cell.set_facecolor('#C6EFCE')  # Green
            elif val >= threshold_med:
                cell.set_facecolor('#FFEB9C')  # Yellow
            else:
                cell.set_facecolor('#FFC7CE')  # Red
        plt.tight_layout()
        plt.savefig("pc_report.png", dpi=200, bbox_inches='tight')

        st.image("pc_report.png", caption="📸 PC Hit WhatsApp Ready")

        with open("pc_report.png", "rb") as f:
            st.download_button("⬇ Download PC Hit Image", f, "pc_report.png")

    else:
        st.info("👆 Upload Telecalling Disbursal Dump to see PC Hit Report")
