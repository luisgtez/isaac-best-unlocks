import logging
import streamlit as st
import ObtainData

logger = logging.Logger("main_logger")

st.title("The Binding of Isaac: Repentance Completion Tracker")

uploaded_file = st.file_uploader("Upload your save", type="dat")
if uploaded_file is not None:
    logger.info(f"File uploaded with filename {uploaded_file.name}")
    try:
        st.dataframe(ObtainData.run_data_parser(uploaded_file.read()))
    except Exception as e:
        st.error("Ups! Something went wrong.")
        logger.error(f"Error when trying to parse the file {uploaded_file.name}. Error:\n\n {e}")
