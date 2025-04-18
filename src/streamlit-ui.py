import logging
import subprocess
from enum import Enum

import streamlit as st
from colorlog import ColoredFormatter
from streamlit_local_storage import LocalStorage

import ObtainData


class AppMode(Enum):
    SAVE_FILE = "Save-File"
    STANDALONE = "Standalone"


def get_git_branch():
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def setup_logger():
    logger = logging.getLogger(__name__)
    branch = get_git_branch()

    if branch == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d @ %(funcName)s - %(message)s",
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

    logger.info(f"Logger setup done. Logger level {logger.level}, branch name {branch}")

    return logger


def lazy_get_or_set_session_state(key, default_value):
    if key not in st.session_state:
        st.session_state[key] = default_value()
    return st.session_state[key]


def get_or_set_session_state(key, default_value):
    if key not in st.session_state:
        logger.debug(f"{key} not in st.session_state")
        st.session_state[key] = default_value
    return st.session_state[key]


class App:

    def __init__(self, logger: logging.Logger):
        self.logger = logger

        self.localStorage: LocalStorage = lazy_get_or_set_session_state(
            "localS", lambda: LocalStorage()
        )
        self.LOADED_COMPLETIONS = get_or_set_session_state("LOADED_COMPLETIONS", False)
        self.logger.debug(
            """
            ##################################################
            #             New App Instace Created            #
            ##################################################
            """
        )

    def read_future_improvements(self):
        try:
            with open("README.md", "r") as f:
                text = f.read()

            future_improvements = text.split("## Future Improvements")[-1]
            future_improvements = future_improvements.split("## Credits")[0]
            future_improvements = "## Future Improvements \n" + future_improvements
            return future_improvements
        except Exception as e:
            self.logger.error(f"Failed to read README.md: {e}")
            return "Error loading future improvements section."

    def process_uploaded_file(self, uploaded_file):
        if "rep+" not in uploaded_file.name:
            st.warning(
                "The save file seems to be from another expansion pack that is not Repentance+. Completion marks for other extension packs are not supported at the time. If you do not have a rep+ save file, we recommend you use the standalone version of the app."
            )

        self.logger.info(f"File uploaded with filename {uploaded_file.name}")
        try:
            df = ObtainData.run_data_parser(uploaded_file.read())
            return df
        except Exception as e:
            self.logger.error(
                f"Error when trying to parse file {uploaded_file.name}. Error:\n\n {e}"
            )
            st.error("Oops! Something went wrong while processing your save file.")
            return None

    def render_choose_app_mode(self):
        st.text("Choose the app mode:")
        col_save_file, col_standalone = st.columns(2, border=True)

        with col_save_file:
            st.markdown("**Save-file mode**")
            st.warning(
                "Currently only save files from Repentance+ work properly and automatically fill in the already completed marks."
            )
            st.markdown(
                "Upload a save file from Repentance+ and have the marks for alredy unlocked items be automatically checked according to your progress."
            )
            st.button(
                "Use save-file mode",
                use_container_width=True,
                on_click=self.set_app_mode,
                args=[AppMode.SAVE_FILE],
            )

        with col_standalone:
            st.markdown("**Standalone mode**")
            st.markdown(
                "Manually check the progress you have done so far without using a save-file. The checks you do in the page stay saved in your browser so you can use this as your progress tracker for your best items unlocks"
            )
            st.button(
                "Use standalone mode",
                use_container_width=True,
                on_click=self.set_app_mode,
                args=[AppMode.STANDALONE],
            )

    def set_app_mode(self, app_mode: AppMode):
        self.logger.debug(f"Setting APP Mode as: {app_mode} - {app_mode.value}")
        st.session_state["APP_MODE"] = app_mode
        self.localStorage.setItem("APP_MODE", app_mode.value)

    def render_save_file_mode(self):
        # st.info("Not sure where your save file is?")
        # st.markdown(
        #     "[Click here for help](https://github.com/luisgtez/isaac-best-unlocks/#where-to-find-the-save-file)",
        #     unsafe_allow_html=True,
        # )

        

        st.html(
            """
            <div style="
                        background-color: #e1f5fe;
                        padding: 1rem;
                        border-left: 5px solid #2196f3;
                        border-radius: 0.5rem;
                        color: #0d47a1;
                        font-family: sans-serif;
                    ">
                💡 Not sure where your save file is?
                <a href="https://github.com/luisgtez/isaac-best-unlocks/#where-to-find-the-save-file"
                    style="color: #0d47a1; text-decoration: underline;">Click here for help</a>
            </div>
            """
        )

        uploaded_file = st.file_uploader("Upload your save", type="dat")

        if uploaded_file is not None:
            result = self.process_uploaded_file(uploaded_file)
            if result is not None:
                st.dataframe(result)

    def render_title_and_header(self):
        st.title("The Binding of Isaac: Repentance+ Completion Tracker")

    def render_footer(self):
        st.markdown(self.read_future_improvements())
        st.markdown(
            """
        ## Issues
        You can submit a ticket with any issues or improvements at the repo's [Issues](https://github.com/luisgtez/isaac-best-unlocks/issues)
        """
        )

    def initialize_variables(self):
        mode = self.localStorage.getItem("APP_MODE")
        if mode == "Save-File":
            self.APP_MODE: AppMode = AppMode.SAVE_FILE
        elif mode == "Standalone":
            self.APP_MODE: AppMode = AppMode.STANDALONE
        elif mode is None:
            self.APP_MODE = None

    def run_page_config(self):
        # st.set_page_config(layout="wide")
        pass

    def reset_app(self):
        st.session_state["APP_MODE"] = None
        self.localStorage.deleteItem("APP_MODE")

        st.rerun()

    def render_app_mode(self):
        if st.button("<- Go back"):
            self.reset_app()

        st.header(f"{self.APP_MODE.value} Mode", anchor=False)

        if self.APP_MODE == AppMode.SAVE_FILE:
            self.render_save_file_mode()

        if self.APP_MODE == AppMode.STANDALONE:
            self.render_standalone_mode()

    def render_standalone_mode(self):
        st.warning(
            "There is currently a bug where the first click on the completed data editor refreshes the page wrongly. But after that it works properly. It is recommended to double click in the first Completed check mark twice before continuing to use the page normally."
        )
        data = b""

        self.logger.debug("Running data parser")
        df = get_or_set_session_state("df", ObtainData.run_data_parser(data))

        disabled_cols = df.columns.to_list()
        disabled_cols.remove("Completed")

        if st.session_state["LOADED_COMPLETIONS"] is False:
            self.logger.debug(
                "LOADED_COMPLETIONS is False. Loading completions from local"
            )
            local_stored_completions = self.localStorage.getItem(
                "standalone-completion-data"
            )
            st.session_state["LOADED_COMPLETIONS"] = True

            if local_stored_completions is not None:
                df["Completed"] = local_stored_completions

        df = st.data_editor(
            df,
            disabled=disabled_cols,
            on_change=self.update_local_stored_completions,
            kwargs={"df": df},
            key="data-editor",
        )

    def update_local_stored_completions(self, df):
        edited_rows = st.session_state["data-editor"].get("edited_rows", {})
        current_completed = df["Completed"].tolist()  # Get current values as a list

        # Update with edited values
        for key, value in edited_rows.items():
            if "Completed" in value:
                current_completed[int(key)] = value["Completed"]

        # Save to local storage
        self.localStorage.setItem("standalone-completion-data", current_completed)

    def render_main_app(self):
        if self.APP_MODE is None:
            self.render_choose_app_mode()
        else:
            self.render_app_mode()

    def run(self):
        self.logger.debug(
            """
            ******************************************
            *               App Running              *
            ******************************************
            """
        )
        self.run_page_config()
        self.initialize_variables()

        self.render_title_and_header()
        self.render_main_app()
        self.render_footer()


if __name__ == "__main__":
    logger = setup_logger()
    app: App = lazy_get_or_set_session_state("app", lambda: App(logger))
    app.run()
