import numpy as np
import pandas as pd
import logging

CHALLENGES_TIERLIST_FILE = "src/data/challenges_data.csv"
NORMAL_UNLOCKS_TIERLIST_FILE = "src/data/normal_characters_unlocks.csv"
TAINED_UNLOCKS_TIERLIST_FILE = "src/data/tainted_characters_unlocks.csv"

# Game data constants
NORMAL_CHARACTERS_INDEX = [
    "Isaac",
    "Magdalene",
    "Cain",
    "Judas",
    "???",
    "Eve",
    "Samson",
    "Azazel",
    "Lazarus",
    "Eden",
    "The Lost",
    "Lilith",
    "Keeper",
    "Apollyon",
    "The Forgotten",
    "Bethany",
    "Jacob & Esau",
]

MARKS_ORDER = [
    "Mom's Heart",
    "Isaac",
    "Satan",
    "Boss Rush",
    "???",
    "The Lamb",
    "Mega Satan",
    "Ultra Greedier",
    "Hush",
    "Delirium",
    "Mother",
    "The Beast",
]

# Create tainted characters index for data processing
TAINTED_CHARACTERS_INDEX = ["-"] * len(
    NORMAL_CHARACTERS_INDEX
) + NORMAL_CHARACTERS_INDEX

# Mapping to interpret completion values in the save file
COMPLETION_MAP = {"0": False, "1": False, "3": True}

logger = logging.getLogger(__name__)


def get_section_offsets(data):
    """Extract section offsets from the save file structure."""
    ofs = 0x14
    sect_data = [-1, -1, -1]
    entry_lens = [1, 4, 4, 1, 1, 1, 1, 4, 4, 1]
    section_offsets = [0] * 10

    for i in range(len(entry_lens)):
        for j in range(3):
            sect_data[j] = int.from_bytes(data[ofs : ofs + 2], "little", signed=False)
            ofs += 4
        if section_offsets[i] == 0:
            section_offsets[i] = ofs
        for j in range(sect_data[2]):
            ofs += entry_lens[i]

    return section_offsets


def get_int(data, offset, debug=False, num_bytes=2):
    """Extract integer of specified byte length from binary data."""
    return int.from_bytes(data[offset : offset + num_bytes], "little")


def get_checklist_unlocks(data, char_index):
    """Extract completion marks for a specific character."""
    checklist_data = []
    section_offsets = get_section_offsets(data)

    # Different offsets based on character index
    if char_index == 14:  # The Forgotten has special offset handling
        clu_ofs = section_offsets[1] + 0x32C
        for i in range(12):
            current_ofs = clu_ofs + i * 4
            checklist_data.append(get_int(data, current_ofs))
            if i == 8:
                clu_ofs += 0x4
            if i == 9:
                clu_ofs += 0x37C
            if i == 10:
                clu_ofs += 0x84
    elif char_index > 14:  # Later characters
        clu_ofs = section_offsets[1] + 0x31C
        for i in range(12):
            current_ofs = clu_ofs + char_index * 4 + i * 19 * 4
            checklist_data.append(get_int(data, current_ofs))
            if i == 8:
                clu_ofs += 0x4C
            if i == 9:
                clu_ofs += 0x3C
            if i == 10:
                clu_ofs += 0x3C
    else:  # Earlier characters
        clu_ofs = section_offsets[1] + 0x6C
        for i in range(12):
            current_ofs = clu_ofs + char_index * 4 + i * 14 * 4
            checklist_data.append(get_int(data, current_ofs))
            if i == 5:
                clu_ofs += 0x14
            if i == 8:
                clu_ofs += 0x3C
            if i == 9:
                clu_ofs += 0x3B0
            if i == 10:
                clu_ofs += 0x50

    return checklist_data


def get_challenges(data):
    """Extract challenge completion data."""
    challenge_data = []
    offs = get_section_offsets(data)[6]
    for i in range(1, 46):
        challenge_data.append(get_int(data, offs + i, num_bytes=1))
    return challenge_data


def check_mark_completion(value):
    """Check if a mark is completed based on its value."""
    return COMPLETION_MAP.get(str(value), False)


def get_character_indices(characters_list):
    """Create a dictionary mapping character names to their indices."""
    return {character: i for i, character in enumerate(characters_list)}


def get_mark_indices():
    """Create a dictionary mapping mark names to their indices."""
    return {mark: i for i, mark in enumerate(MARKS_ORDER)}


def get_character_completion_marks(data, character_name, character_indices):
    """Get all completion marks for a specific character."""
    character_index = character_indices[character_name]
    return get_checklist_unlocks(data, character_index)


def process_normal_character_marks(data, tierlist_df):
    """Process completion marks for normal characters."""
    character_indices = get_character_indices(NORMAL_CHARACTERS_INDEX)
    mark_indices = get_mark_indices()
    completion_marks = {}
    completion_results = []

    for _, row in tierlist_df.iterrows():
        character_name = row["Character"]
        mark_name = row["Mark"]

        # Convert Ultra Greed to Ultra Greedier for hard mode
        if mark_name == "Ultra Greed":
            mark_name = "Ultra Greedier"

        # Fetch character marks if not already cached
        if character_name not in completion_marks:
            completion_marks[character_name] = get_character_completion_marks(
                data, character_name, character_indices
            )

        marks = completion_marks[character_name]

        if mark_name == "All Marks":
            # Check if all marks are completed
            all_marks_completed = all(value == 3 for value in marks)
            completion_results.append(all_marks_completed)
        else:
            # Get individual mark completion
            mark_index = mark_indices[mark_name]
            completed = check_mark_completion(marks[mark_index])
            completion_results.append(completed)

    return completion_results


def process_tainted_character_marks(data, tierlist_df):
    """Process completion marks for tainted characters."""
    character_indices = get_character_indices(TAINTED_CHARACTERS_INDEX)
    mark_indices = get_mark_indices()
    completion_marks = {}
    completion_results = []

    for _, row in tierlist_df.iterrows():
        character_name = row["Character"]
        mark_name = row["Mark"]

        # Fetch character marks if not already cached
        if character_name not in completion_marks:
            completion_marks[character_name] = get_character_completion_marks(
                data, character_name, character_indices
            )

        marks = completion_marks[character_name]

        # Process special completion conditions
        if mark_name == "Boss Rush & Hush":
            completed = check_mark_completion(
                marks[mark_indices["Boss Rush"]]
            ) and check_mark_completion(marks[mark_indices["Hush"]])
        elif mark_name == "Isaac, ???, Satan, Lamb":
            completed = (
                check_mark_completion(marks[mark_indices["Isaac"]])
                and check_mark_completion(marks[mark_indices["???"]])
                and check_mark_completion(marks[mark_indices["Satan"]])
                and check_mark_completion(marks[mark_indices["The Lamb"]])
            )
        else:
            mark_index = mark_indices[mark_name]
            completed = check_mark_completion(marks[mark_index])

        completion_results.append(completed)

    return completion_results


def prepare_dataframe(df):
    """Clean and prepare dataframe columns."""
    df.columns = df.columns.str.strip()
    return df


def unify_results(challenges_df, normal_df, tainted_df):
    """Unify the results from all dataframes into a single dataframe."""
    # Prepare individual dataframes
    challenges_df = prepare_dataframe(challenges_df)
    normal_df = prepare_dataframe(normal_df)
    tainted_df = prepare_dataframe(tainted_df)

    # Adjust scales and add prefixes
    challenges_df["Reward"] = challenges_df["Reward"] - 1
    tainted_df["Character"] = tainted_df["Character"].apply(lambda x: f"Tainted {x}")

    # Concatenate all dataframes
    all_data = np.concat(
        [
            challenges_df[["Nº", "Name", "Reward", "Item","Type", "Completed"]].values,
            normal_df.values,
            tainted_df.values,
        ],
        axis=0,
    )

    # Create unified dataframe with consistent column names
    all_df = pd.DataFrame(
        all_data,
        columns=["Nº/Character", "Name/Mark", "Quality", "Item", "Type", "Completed"],
    )

    # Clean and standardize data types
    all_df = all_df.map(lambda x: x.strip() if isinstance(x, str) else x)
    all_df["Nº/Character"] = all_df["Nº/Character"].astype(str)
    all_df["Name/Mark"] = all_df["Name/Mark"].astype(str)
    all_df["Quality"] = all_df["Quality"].astype(int)
    all_df["Item"] = all_df["Item"].astype(str)
    all_df["Completed"] = all_df["Completed"].astype(bool)

    return all_df


def getSecrets(data):
    """
    Get the status of all secrets/achievements from the save file.
    Copied from script.py to remove dependency.
    """
    secrets_data = []
    offs = get_section_offsets(data)[0]
    for i in range(1, 638):
        secrets_data.append(get_int(data, offs+i, num_bytes=1))
    return secrets_data


def get_unlocked_characters(data):
    """
    Returns a list of characters that are unlocked in the save file.
    
    Args:
        data: Binary save file data
        
    Returns:
        list: Names of unlocked characters
    """
    # Character unlock achievement IDs
    character_unlock_secrets = {
        "Magdalene": 1,
        "Cain": 2,
        "Judas": 3,
        "???": 32,
        "Eve": 42,
        "Samson": 67,
        "Azazel": 79,
        "Lazarus": 80,
        "Eden": 81,
        "The Lost": 82,
        "Lilith": 199,
        "Keeper": 251,
        "Apollyon": 340,
        "The Forgotten": 390,
        "Bethany": 404,
        "Jacob & Esau": 405,
        # Tainted characters with known IDs
        "Tainted Cain": 514,
        "Tainted Forgotten": 513,
        "Tainted Eden": 516,
        "Tainted Jacob & Esau": 515
    }
    
    # Isaac is unlocked by default
    unlocked_characters = ["Isaac"]
    
    try:
        # Get secrets (achievements) using the copied function
        secrets = getSecrets(data)
        
        # Check which characters are unlocked
        for character, secret_id in character_unlock_secrets.items():
            # Need to check index-1 since achievements are 1-indexed in the IDs but 0-indexed in the array
            if secret_id-1 < len(secrets) and secrets[secret_id-1] == 1:
                unlocked_characters.append(character)
    except Exception as e:
        logger.error(f"Error getting unlocked characters: {e}")
    
    return unlocked_characters


def run_data_parser(save_data):
    """Main function to process save data and return unified results."""
    # File paths
    challenges_tierlist_file = CHALLENGES_TIERLIST_FILE
    normal_unlocks_tierlist_file = NORMAL_UNLOCKS_TIERLIST_FILE
    tainted_unlocks_tierlist_file = TAINED_UNLOCKS_TIERLIST_FILE
    # challenges_tierlist_file = "src/data/challenges_data.csv"
    # normal_unlocks_tierlist_file = "src/data/normal_characters_unlocks.csv"
    # tainted_unlocks_tierlist_file = "src/data/tainted_characters_unlocks.csv"

    # Load CSV data
    challenges_tierlist_df = pd.read_csv(challenges_tierlist_file)
    normal_unlocks_tierlist_df = pd.read_csv(normal_unlocks_tierlist_file)
    tainted_unlocks_tierlist_df = pd.read_csv(tainted_unlocks_tierlist_file)

    # Process challenges
    challenges_completed = get_challenges(save_data)
    challenges_tierlist_df["Completed"] = challenges_completed
    challenges_tierlist_df["Completed"] = challenges_tierlist_df["Completed"].astype(
        bool
    )
    challenges_tierlist_df["Type"] = "Challenge"
    normal_unlocks_tierlist_df["Type"] = "Unlock"
    tainted_unlocks_tierlist_df["Type"] = "Unlock"

    # Process character completion marks
    normal_completions = process_normal_character_marks(
        save_data, normal_unlocks_tierlist_df
    )
    normal_unlocks_tierlist_df["Completed"] = normal_completions

    tainted_completions = process_tainted_character_marks(
        save_data, tainted_unlocks_tierlist_df
    )
    tainted_unlocks_tierlist_df["Completed"] = tainted_completions
    # Unify results
    all_df = unify_results(
        challenges_tierlist_df, normal_unlocks_tierlist_df, tainted_unlocks_tierlist_df
    )
    
    # Get unlocked characters
    unlocked_characters = get_unlocked_characters(save_data)
    
    # Add unlocked status info to the results
    all_df["Unlocked"] = False
    
    # Mark characters as unlocked
    for character in unlocked_characters:
        # For normal characters
        if character in NORMAL_CHARACTERS_INDEX:
            all_df.loc[all_df["Nº/Character"] == character, "Unlocked"] = True
        # For tainted characters (they have "Tainted " prefix in the dataframe)
        elif character.startswith("Tainted ") and character[8:] in NORMAL_CHARACTERS_INDEX:
            all_df.loc[all_df["Nº/Character"] == character, "Unlocked"] = True
    
    # Mark challenges as unlocked - All challenges are unlocked by default in Repentance+
    # If this is not the case in all versions, we could modify this logic
    all_df.loc[all_df["Type"] == "Challenge", "Unlocked"] = True
    
    return all_df
