import logging
import subprocess
from enum import Enum

import streamlit as st
from colorlog import ColoredFormatter
from streamlit_local_storage import LocalStorage

import ObtainData


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
    if "logger" in st.session_state:

        return st.session_state["logger"]

    logger = logging.getLogger(__name__)
    branch = get_git_branch()

    if branch == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] @ %(funcName)s - %(message)s",
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

        st.session_state["logger"] = logger
        logger.debug(
            "Logger setup done. Logger level %s, branch name %s", logger.level, branch
        )

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

    def run_page_config(self):
        # st.set_page_config(layout="wide")
        pass



    def get_df(self, data=None):
        if data is None:
            data = b""
        
        self.logger.debug("Running data parser")
        
        # Update DataFrame if new data is provided or if it doesn't exist in session state
        if data and len(data) > 0:
            self.logger.debug("New save file uploaded, updating DataFrame")
            full_df = ObtainData.run_data_parser(data)
            st.session_state["full_df"] = full_df
        elif "full_df" not in st.session_state:
            self.logger.debug("Creating new DataFrame")
            full_df = ObtainData.run_data_parser(data)
            st.session_state["full_df"] = full_df
        else:
            # Use existing full DataFrame
            full_df = st.session_state["full_df"]
        
        disabled_cols = full_df.columns.to_list()
        disabled_cols.remove("Completed")

        # Load completions from local storage and apply to the full DataFrame
        if st.session_state["LOADED_COMPLETIONS"] is False:
            self.logger.debug(
                "LOADED_COMPLETIONS is False. Loading completions from local"
            )
            local_stored_completions = self.localStorage.getItem(
                "standalone-completion-data"
            )
            st.session_state["LOADED_COMPLETIONS"] = True

            if local_stored_completions is not None:
                try:
                    # Check if lengths match
                    if len(local_stored_completions) == len(full_df):
                        full_df["Completed"] = local_stored_completions
                        st.session_state["full_df"] = full_df
                    else:
                        self.logger.warning(
                            f"Stored completions length ({len(local_stored_completions)}) "
                            f"doesn't match DataFrame length ({len(full_df)}). "
                            "Skipping load of stored completions."
                        )
                except Exception as e:
                    self.logger.error(f"Error applying stored completions: {e}")

        return full_df, disabled_cols

    def filter_df(self, df):
        # Create a copy of the DataFrame to avoid modifying the original
        filtered_df = df.copy()
        
        col_completed, col_unlocked, col_tainted = st.columns(3)
        # Completed filter
        with col_completed:
            completed_filter = st.checkbox("Hide completed items", value=True)
            if completed_filter:
                filtered_df = filtered_df[filtered_df["Completed"] == 0]

        # Show only unlocked characters/challenges filter
        with col_unlocked:
            unlocked_filter = st.checkbox("Show only unlocked content", value=True, help="Challenges are always counted as unlocked")
            if unlocked_filter and "Unlocked" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Unlocked"] == True]
        
        # Hide tainted characters filter
        with col_tainted:
            tainted_filter = st.checkbox(
                "Hide tainted characters", 
                value=False,
                help="Tainted character detection is not fully supported yet"
            )
        # Type filter
        col_type, col_sort, col_config_unlocked = st.columns(3)
        with col_type:
            type_filter = st.selectbox(
                "Select unlock types", ["All"] + filtered_df["Type"].unique().tolist()
            )
            if type_filter == "All":
                pass
            else:
                filtered_df = filtered_df[filtered_df["Type"] == type_filter]



            if tainted_filter:
                # Filter out rows where Character/Nº starts with "Tainted"
                filtered_df = filtered_df[~filtered_df["Nº/Character"].astype(str).str.startswith("Tainted")]

        with col_sort:
            if st.checkbox("Sort by best quality", value=True):
                filtered_df = filtered_df.sort_values(by="Quality", ascending=False)

        return filtered_df

    def render_main(self):
        st.warning(
            "There is currently a bug where the first click on the completed data editor refreshes the page wrongly. But after that it works properly. It is recommended to double click in the first Completed check mark twice before continuing to use the page normally."
        )

        # Load save file first (this will update session state if a file is uploaded)
        data = self.load_save_file()
        
        # Add debug logging to see if data is being received
        if data:
            self.logger.debug(f"Save file loaded, data length: {len(data)} bytes")
        else:
            self.logger.debug("No save file loaded or empty data")

        # Get full DataFrame
        full_df, disabled_cols = self.get_df(data)
        
        # Log DataFrame shape to verify it's being updated
        self.logger.debug(f"Full DataFrame shape: {full_df.shape}")
        
        # Apply filters to create display DataFrame
        filtered_df = self.filter_df(full_df)
        self.logger.debug(f"Filtered DataFrame shape: {filtered_df.shape}")

        # Display filtered DataFrame
        edited_df = st.data_editor(
            filtered_df,
            disabled=disabled_cols,
            on_change=self.update_local_stored_completions,
            kwargs={"full_df": full_df, "filtered_df": filtered_df},
            key="data-editor",
        )

    def initialize_variables(self):
        self.LOADED_COMPLETIONS = get_or_set_session_state("LOADED_COMPLETIONS", False)
        # Initialize file metadata from local storage if available
        self.load_file_metadata_from_storage()

    def load_file_metadata_from_storage(self):
        """Load saved file metadata and data from local storage"""
        try:
            # Get file metadata from localStorage
            file_name = self.localStorage.getItem("saved_file_name")
            file_data_base64 = self.localStorage.getItem("saved_file_data")
            
            if file_name and file_data_base64:
                # Convert base64 string back to bytes
                import base64
                file_data = base64.b64decode(file_data_base64)
                
                # Store in session state
                st.session_state["uploaded_file_name"] = file_name
                st.session_state["file_uploaded"] = True
                st.session_state["save_data"] = file_data
                
                self.logger.debug(f"Loaded file '{file_name}' from local storage, size: {len(file_data)} bytes")
        except Exception as e:
            self.logger.error(f"Error loading file from local storage: {e}")
            # Reset if there's an error
            self.localStorage.setItem("saved_file_name", None, key="saved_file_name_load_file_metadata")
            self.localStorage.setItem("saved_file_data", None, key="saved_file_data_load_file_metadata")

    def save_file_to_storage(self, file_name, file_data):
        """Save file metadata and data to local storage"""
        try:
            # Convert binary data to base64 string for storage
            import base64
            file_data_base64 = base64.b64encode(file_data).decode('utf-8')
            
            # Save to localStorage
            self.localStorage.setItem("saved_file_name", file_name, key="saved_file_name_save_file_to_storage")
            self.localStorage.setItem("saved_file_data", file_data_base64, key="saved_file_data_save_file_to_storage")
            
            self.logger.debug(f"Saved file '{file_name}' to local storage, size: {len(file_data)} bytes")
        except Exception as e:
            self.logger.error(f"Error saving file to local storage: {e}")

    def load_save_file(self):
        # Initialize file_uploaded_state if it doesn't exist
        if "file_uploaded" not in st.session_state:
            st.session_state["file_uploaded"] = False
        
        # Initialize file metadata storage if it doesn't exist
        if "uploaded_file_name" not in st.session_state:
            st.session_state["uploaded_file_name"] = None
        if "save_data" not in st.session_state:
            st.session_state["save_data"] = None
            
        # Create file uploader with a key
        uploaded_file = st.file_uploader(
            "Upload your save", 
            type="dat", 
            key="save_file_uploader",
            # Show label of the previously uploaded file if available
            label_visibility="visible" if not st.session_state["uploaded_file_name"] else "collapsed"
        )

        # Handle file upload first
        if uploaded_file is not None:
            # Process the newly uploaded file
            file_name = uploaded_file.name
            st.session_state["uploaded_file_name"] = file_name
            
            if "rep+" not in file_name:
                st.warning(
                    "The save file seems to be from another expansion pack that is not Repentance+. Completion marks for other extension packs are not supported at the time. If you do not have a rep+ save file, we recommend you use the standalone version of the app."
                )
            
            # Mark that a file has been uploaded
            st.session_state["file_uploaded"] = True
            file_data = uploaded_file.read()
            st.session_state["save_data"] = file_data
            
            # Save to local storage for persistence
            self.save_file_to_storage(file_name, file_data)
            
            # Show success message immediately for the uploaded file
            st.success(f"File uploaded: {file_name}")
            
            # Always show the remove button right after upload
            if st.button("Remove uploaded file", key="remove_button_upload"):
                st.session_state["uploaded_file_name"] = None
                st.session_state["file_uploaded"] = False
                st.session_state["save_data"] = None
                
                # Clear from local storage
                self.localStorage.deleteItem("saved_file_name", key="saved_file_name_remove_uploaded_file")
                self.localStorage.deleteItem("saved_file_data", key="saved_file_data_remove_uploaded_file")
                
                if "full_df" in st.session_state:
                    del st.session_state["full_df"]
                st.rerun()
                
            # Return the file data for processing
            return file_data
            
        # Handle previously uploaded file case
        elif st.session_state["uploaded_file_name"]:
            # Show message for previously uploaded file
            st.success(f"Using previously uploaded file: {st.session_state['uploaded_file_name']}")
            
            # Show remove button for previously uploaded file
            if st.button("Remove uploaded file", key="remove_button_previous"):
                st.session_state["uploaded_file_name"] = None
                st.session_state["file_uploaded"] = False
                st.session_state["save_data"] = None
                
                # Clear from local storage
                self.localStorage.deleteItem("saved_file_name", key="saved_file_name")
                self.localStorage.deleteItem("saved_file_data", key="saved_file_data")
                
                if "full_df" in st.session_state:
                    del st.session_state["full_df"]
                st.rerun()
            
            # Return previously saved data if available
            if st.session_state["save_data"] is not None:
                return st.session_state["save_data"]
        
        # Reset state if no file is found
        if uploaded_file is None and st.session_state.get("file_uploaded", False) and not st.session_state.get("uploaded_file_name"):
            st.session_state["file_uploaded"] = False
            st.session_state["save_data"] = None
            # Remove from local storage
            self.localStorage.setItem("saved_file_name", None, key="saved_file_name_remove_uploaded_file")
            self.localStorage.setItem("saved_file_data", None, key="saved_file_data_remove_uploaded_file")
            # Remove DataFrame from session state to ensure a fresh start if needed
            if "full_df" in st.session_state:
                del st.session_state["full_df"]


    def update_local_stored_completions(self, full_df, filtered_df):
        edited_rows = st.session_state["data-editor"].get("edited_rows", {})
        
        # If we have edited rows, update both the filtered and full DataFrames
        if edited_rows:
            self.logger.debug(f"Updating {len(edited_rows)} edited rows")
            
            # Keep track of changes to full_df
            full_df_changes = []
            
            # Process each edited row
            for row_idx, changes in edited_rows.items():
                if "Completed" in changes:
                    # Get the actual row index from the full DataFrame
                    # We need to map from the filtered_df index to the full_df index
                    filtered_row_idx = int(row_idx)
                    row_key = filtered_df.iloc[filtered_row_idx].name
                    
                    # Update the full DataFrame at the correct index
                    full_df.at[row_key, "Completed"] = changes["Completed"]
                    full_df_changes.append((row_key, changes["Completed"]))
            
            # Update session state with the modified full DataFrame
            st.session_state["full_df"] = full_df
            
            # Save the full DataFrame's completions to local storage
            self.localStorage.setItem("standalone-completion-data", full_df["Completed"].tolist(), key="standalone-completion-data_update_local_stored_completionsru")

    def run(self):
        self.logger.debug(
            """
            ******************************************
            *               App Running              *
            ******************************************
            """
        )
        self.initialize_variables()
        self.run_page_config()

        self.format_filters()

        self.render_title_and_header()
        self.render_main()
        self.render_footer()

    def format_filters(self):
        st.html("""
        <style>
        .stVerticalBlock > div:nth-of-type(7) {
            align-items: center;
        }
        </style>
        """)


if __name__ == "__main__":
    logger = setup_logger()
    app: App = lazy_get_or_set_session_state("app", lambda: App(logger))
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running app: {e}")
        st.error(f"Error running app: {e}")
