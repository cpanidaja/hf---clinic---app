import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="HF Clinic Master Tracker v2", layout="wide")

# ฟังก์ชันคำนวณ eGFR (CKD-EPI 2021)
def calculate_egfr(scr, age, gender):
    if scr == 0: return 0
    kappa = 0.7 if gender == "Female" else 0.9
    alpha = -0.241 if gender == "Female" else -0.302
    gender_constant = 1.012 if gender == "Female" else 1.0
    egfr = 142 * (min(scr / kappa, 1) ** alpha) * (max(scr / kappa, 1) ** -1.200) * (0.9938 ** age) * gender_constant
    return round(egfr, 2)

def save_to_excel(new_data):
    file_name = 'hf_complete_records.xlsx'
    if os.path.exists(file_name):
        df = pd.read_excel(file_name)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    else:
        df = pd.DataFrame([new_data])
    df.to_excel(file_name, index=False)

st.title("🏥 HF Clinic: Pharmaceutical Care Management System")

# ส่วนที่เพิ่มเข้ามา: รายชื่อเภสัชกร (สามารถแก้ไขชื่อในลิสต์นี้ได้เลย)
pharmacist_list = ["ภก. สมชาย ใจดี", "ภญ. สมหญิง รักเรียน", "อื่นๆ (ระบุเอง)"]

menu = ["บันทึกการบริบาลใหม่", "ตารางนัดหมายวันนี้", "ฐานข้อมูลและรายงาน"]
choice = st.sidebar.selectbox("เมนูหลัก", menu)

if choice == "บันทึกการบริบาลใหม่":
    with st.form("main_form", clear_on_submit=True):
        # เพิ่มส่วนเลือกชื่อเภสัชกรที่ด้านบนสุด
        st.subheader("👨‍⚕️ ข้อมูลผู้บันทึก")
        c_staff1, c_staff2 = st.columns(2)
        with c_staff1:
            recorder_name = st.selectbox("ชื่อเภสัชกรผู้บันทึก", pharmacist_list)
        with c_staff2:
            if recorder_name == "อื่นๆ (ระบุเอง)":
                recorder_name = st.text_input("ระบุชื่อ-นามสกุล ภก./ภญ.")

        st.divider()
        st.subheader("1. ข้อมูลผู้ป่วยและผลเลือด")
        c1, c2, c3 = st.columns(3)
        with c1:
            hn = st.text_input("HN")
            age = st.number_input("อายุ (ปี)", 18, 110, 60)
            gender = st.radio("เพศ", ["Male", "Female"], horizontal=True)
        with c2:
            scr = st.number_input("Scr (mg/dL)", 0.1, 15.0, 1.0)
            egfr_val = calculate_egfr(scr, age, gender)
            st.metric("eGFR (ml/min)", f"{egfr_val}")
            k_val = st.number_input("Potassium (mEq/L)", 2.0, 7.0, 4.0)
        with c3:
            lvef = st.number_input("LVEF (%)", 5, 80, 40)
            nyha = st.selectbox("NYHA Class", ["I", "II", "III", "IV"])

        st.divider()
        st.subheader("2. ปัญหาจากการใช้ยา (DRPs) และการจัดการ")
        d1, d2 = st.columns(2)
        with d1:
            drp_prob = st.selectbox("ปัญหาที่พบ (Problem)", ["No DRP", "P1: Effectiveness", "P2: Safety", "P3: Adherence"])
            drp_cause = st.selectbox("สาเหตุ (Cause)", ["C1: Dose too low", "C2: ADRs", "C3: Patient forgets", "C4: New indication"])
        with d2:
            intervention = st.text_area("การดำเนินการ (Intervention)")
            
        st.divider()
        st.subheader("3. การนัดหมายติดตามผล (Follow-up)")
        f1, f2 = st.columns(2)
        with f1:
            next_visit = st.date_input("วันนัดครั้งถัดไป", datetime.now() + timedelta(days=30))
        with f2:
            follow_up_topic = st.multiselect("หัวข้อที่ต้องติดตามพิเศษ", ["Titration", "Lab (K/Cr)", "Adherence", "Clinical Symptoms"])

        if st.form_submit_button("บันทึกข้อมูลทั้งหมด"):
            data = {
                "Record_Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Pharmacist": recorder_name, # เก็บชื่อเภสัชกรลง Database
                "HN": hn, "Age": age, "Gender": gender, "eGFR": egfr_val, "K": k_val,
                "LVEF": lvef, "NYHA": nyha, "DRP": drp_prob, "Intervention": intervention,
                "Next_Visit": next_visit.strftime("%Y-%m-%d"),
                "Follow_up_Topic": ", ".join(follow_up_topic)
            }
            save_to_excel(data)
            st.success(f"บันทึกข้อมูลโดย {recorder_name} เรียบร้อยแล้ว!")

elif choice == "ตารางนัดหมายวันนี้":
    st.subheader("📅 รายชื่อผู้ป่วยที่ต้องติดตามวันนี้")
    if os.path.exists('hf_complete_records.xlsx'):
        df = pd.read_excel('hf_complete_records.xlsx')
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = df[df['Next_Visit'] == today]
        
        if not upcoming.empty:
            st.write(f"พบนัดหมายทั้งหมด {len(upcoming)} ราย")
            # แสดงชื่อเภสัชกรที่เคยบันทึกไว้ด้วย เพื่อให้รู้ว่าใครเป็นเจ้าของเคส
            st.table(upcoming[['HN', 'Next_Visit', 'Follow_up_Topic', 'Pharmacist']])
        else:
            st.info("วันนี้ไม่มีผู้ป่วยนัดหมาย")
    else:
        st.warning("ยังไม่มีฐานข้อมูล")

elif choice == "ฐานข้อมูลและรายงาน":
    st.subheader("📂 ประวัติการบริบาลทั้งหมด")
    if os.path.exists('hf_complete_records.xlsx'):
        df = pd.read_excel('hf_complete_records.xlsx')
        # แสดงตารางพร้อมคอลัมน์ชื่อเภสัชกร
        st.dataframe(df)
        
        # สรุปผลงานแยกตามรายชื่อเภสัชกร
        st.subheader("📈 สรุปผลงานแยกตามเภสัชกร (Intervention Count)")
        st.bar_chart(df['Pharmacist'].value_counts())
        
        with open("hf_complete_records.xlsx", "rb") as f:
            st.download_button("📥 Export to Excel", f, "HF_Clinic_Master.xlsx")