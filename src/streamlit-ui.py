import logging
import streamlit as st
import ObtainData
from colorlog import ColoredFormatter



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

st.title("The Binding of Isaac: Repentance Completion Tracker")

st.warning("Currently only 'rep+persistentgamedata<PROFILE_NUM>.dat' save files have been tested. App and completition marks based on this may not work properly for other versions.")
uploaded_file = st.file_uploader("Upload your save", type="dat")
if uploaded_file is not None:
    logger.info(f"File uploaded with filename {uploaded_file.name}")
    try:
        st.dataframe(ObtainData.run_data_parser(uploaded_file.read()))
    except Exception as e:
        st.error("Ups! Something went wrong.")
        logger.error(f"Error when trying to parse the file {uploaded_file.name}. Error:\n\n {e}")
