import logging
import streamlit as st
import ObtainData
from colorlog import ColoredFormatter


def read_future_improvements():
    with open("README.md", "r") as f:
        text = f.read()

    future_improvements = text.split("## Future Improvements")[-1]
    future_improvements = future_improvements.split("## Credits")[0]
    future_improvements = "## Future Improvements \n" + future_improvements

    return future_improvements


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

st.title("The Binding of Isaac: Repentance+ Completion Tracker")

st.warning(
    "Currently only save files from Repentance+ work properly and automatically fill the alredy completed marks in. \n\n" \
    "While there is no plan to add compatibility with save file from previous DLC for now, a manual mode where one can manually check the completion marks is currently under construction."
)

uploaded_file = st.file_uploader("Upload your save", type="dat")
if uploaded_file is not None:
    if not uploaded_file.name.startswith("rep+"):
        st.warning("The save file seems to be from other expansion pack that is not Repentance+, completition marks may not properly be automatically checked.")
    logger.info(f"File uploaded with filename {uploaded_file.name}")
    try:
        st.dataframe(ObtainData.run_data_parser(uploaded_file.read()))
    except Exception as e:
        st.error("Ups! Something went wrong.")
        logger.error(
            f"Error when trying to parse the file {uploaded_file.name}. Error:\n\n {e}"
        )

st.markdown(read_future_improvements())

st.markdown(
    """
## Issues
You can submit a ticket with any issues or improvements at the repo's [Issues](https://github.com/luisgtez/isaac-best-unlocks/issues)
"""
)
