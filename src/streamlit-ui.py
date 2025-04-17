import logging

import streamlit as st
from colorlog import ColoredFormatter

import ObtainData


def setup_logger():
    """Configure and return a colored logger instance."""
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

    return logger


def read_future_improvements():
    """Extract the Future Improvements section from README.md."""
    try:
        with open("README.md", "r") as f:
            text = f.read()

        future_improvements = text.split("## Future Improvements")[-1]
        future_improvements = future_improvements.split("## Credits")[0]
        future_improvements = "## Future Improvements \n" + future_improvements

        return future_improvements
    except Exception as e:
        logger.error(f"Failed to read README.md: {e}")
        return "Error loading future improvements section."


def process_uploaded_file(uploaded_file):
    """Process the uploaded save file and return dataframe."""
    if "rep+" not in uploaded_file.name:
        st.warning(
            "The save file seems to be from another expansion pack that is not Repentance+. Completion marks may not be automatically checked properly."
        )

    logger.info(f"File uploaded with filename {uploaded_file.name}")

    try:
        return ObtainData.run_data_parser(uploaded_file.read())
    except Exception as e:
        logger.error(
            f"Error when trying to parse file {uploaded_file.name}. Error:\n\n {e}"
        )
        st.error("Oops! Something went wrong while processing your save file.")
        return None


def main():
    """Main application function."""
    st.title("The Binding of Isaac: Repentance+ Completion Tracker")

    st.warning(
        "Currently only save files from Repentance+ work properly and automatically fill in the already completed marks.\n\n"
        "While there is no plan to add compatibility with save files from previous DLCs for now, "
        "a manual mode where one can manually check the completion marks is currently under construction."
    )

    # File upload section
    uploaded_file = st.file_uploader("Upload your save", type="dat")
    if uploaded_file is not None:
        result = process_uploaded_file(uploaded_file)
        if result is not None:
            st.dataframe(result)

    # Documentation sections
    st.markdown(read_future_improvements())

    st.markdown(
        """
    ## Issues
    You can submit a ticket with any issues or improvements at the repo's [Issues](https://github.com/luisgtez/isaac-best-unlocks/issues)
    """
    )


if __name__ == "__main__":
    logger = setup_logger()
    main()
