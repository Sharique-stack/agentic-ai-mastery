# day13_dashboard.py - Day 13 Beautiful Analytics Dashboard (Streamlit)
# Deploy this on Streamlit Cloud FREE - separate from Render bot

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import os

st.set_page_config(
    page_title="Day 13 - Tutor Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Day 13 - WhatsApp Tutor Analytics Dashboard")
st.caption("Live from leads.db | Day 13 - C Analytics Track")

# Check DB exists
DB_PATH = "leads.db"
if not os.path.exists(DB_PATH):
    st.warning("⚠️ No leads.db yet. Send a WhatsApp message to your bot first, then refresh.")
    st.info("Your bot must be live at: https://preply-whatsapp-bot.onrender.com/twilio")
    st.stop()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        leads = pd.read_sql_query("SELECT * FROM leads ORDER BY timestamp DESC", conn)
    except Exception as e:
        leads = pd.DataFrame()
    try:
        bookings = pd.read_sql_query("SELECT * FROM bookings ORDER BY timestamp DESC", conn)
    except:
        bookings = pd.DataFrame()
    conn.close()
    return leads, bookings

leads_df, bookings_df = load_data()

# ===== TOP METRICS =====
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💬 Total Chats", len(leads_df))
with col2:
    st.metric("📅 Total Bookings", len(bookings_df))
with col3:
    conv = f"{len(bookings_df)/len(leads_df)*100:.1f}%" if len(leads_df) > 0 else "0%"
    st.metric("📈 Conversion", conv)
with col4:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_leads = len(leads_df[leads_df['timestamp'].str.contains(today_str, na=False)]) if not leads_df.empty else 0
    st.metric("🔥 Today", today_leads)

st.divider()

# ===== TWO COLUMNS =====
left, right = st.columns(2)

with left:
    st.subheader("💬 Recent WhatsApp Leads")
    if not leads_df.empty:
        st.dataframe(
            leads_df[['student_name','phone','query','timestamp','booked']].head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No chats yet. Send 'hi' to +1 415 523 8886 on WhatsApp")

with right:
    st.subheader("📅 Recent Bookings")
    if not bookings_df.empty:
        st.dataframe(
            bookings_df[['student_name','phone','time','timestamp']].head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No bookings yet")

st.divider()

# ===== CHARTS =====
st.subheader("📊 Insights")

if not leads_df.empty:
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Top Students (by messages)**")
        st.bar_chart(leads_df['student_name'].value_counts().head(10))
    
    with col_b:
        st.write("**Bookings vs Chats**")
        chart_data = pd.DataFrame({
            "Type": ["Chats", "Bookings"],
            "Count": [len(leads_df), len(bookings_df)]
        })
        st.bar_chart(chart_data, x="Type", y="Count")
    
    st.write("**All Queries (Word Cloud Text)**")
    all_text = " ".join(leads_df['query'].astype(str).tolist())[:1000]
    st.code(all_text, language="text")
else:
    st.write("Charts will appear after data comes in")

# Footer
st.divider()
st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: Enable in Streamlit settings | DB: {DB_PATH}")
if st.button("🔄 Refresh Data"):
    st.rerun()