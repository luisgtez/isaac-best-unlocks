import streamlit as st
import ObtainData

st.title("The Binding of Isaac: Repentance Completion Tracker")

uploaded_file = st.file_uploader("Upload your save", type="dat")
if uploaded_file is not None:
    st.dataframe(ObtainData.run_data_parser(uploaded_file.read()))