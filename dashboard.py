import streamlit as st
import pandas as pd
import time

st.title("🚗 Driver Monitoring Dashboard")

while True:
    try:
        df = pd.read_csv("live_data.csv")

        fatigue = int(df["fatigue"][0])
        attention = int(df["attention"][0])

        st.metric("Fatigue Score", fatigue)
        st.metric("Attention Score", attention)

        st.line_chart(df)

        time.sleep(1)
        st.rerun()

    except:
        st.write("Waiting for data...")