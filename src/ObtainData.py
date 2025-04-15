import pandas as pd
import numpy as np

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
    if debug:
        print(
            f"current value: {int.from_bytes(data[offset:offset+num_bytes], 'little', signed=False)}"
        )
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


def process_normal_character_marks(data, tierlist_df):
    """Process completion marks for normal characters."""
    character_indices = {
        character: i for i, character in enumerate(NORMAL_CHARACTERS_INDEX)
    }
    mark_indices = {mark: i for i, mark in enumerate(MARKS_ORDER)}
    completion_marks = {}
    completion_results = []

    for _, row in tierlist_df.iterrows():
        character_name = row["Character"]
        mark_name = row["Mark"]

        # Convert Ultra Greed to Ultra Greedier for hard mode
        if mark_name == "Ultra Greed":
            mark_name = "Ultra Greedier"

        if mark_name != "All Marks":
            # Get individual mark completion
            character_index = character_indices[character_name]
            mark_index = mark_indices[mark_name]

            if character_name not in completion_marks:
                completion_marks[character_name] = get_checklist_unlocks(
                    data, character_index
                )

            completed = COMPLETION_MAP.get(
                str(completion_marks[character_name][mark_index]), False
            )
            completion_results.append(completed)
        else:
            # Check if all marks are completed
            character_index = character_indices[character_name]
            if character_name not in completion_marks:
                completion_marks[character_name] = get_checklist_unlocks(
                    data, character_index
                )

            all_marks_completed = all(
                value == 3 for value in completion_marks[character_name]
            )
            completion_results.append(all_marks_completed)

    return completion_results


def process_tainted_character_marks(data, tierlist_df):
    """Process completion marks for tainted characters."""
    character_indices = {
        character: i for i, character in enumerate(TAINTED_CHARACTERS_INDEX)
    }
    mark_indices = {mark: i for i, mark in enumerate(MARKS_ORDER)}
    completion_marks = {}
    completion_results = []

    for _, row in tierlist_df.iterrows():
        character_name = row["Character"]
        mark_name = row["Mark"]

        char_index = character_indices[character_name]
        if character_name not in completion_marks:
            completion_marks[character_name] = get_checklist_unlocks(data, char_index)

        marks = completion_marks[character_name]

        if mark_name == "Boss Rush & Hush":
            completed = (
                marks[MARKS_ORDER.index("Boss Rush")] == 3
                and marks[MARKS_ORDER.index("Hush")] == 3
            )
        elif mark_name == "Isaac, ???, Satan, Lamb":
            completed = (
                marks[MARKS_ORDER.index("Isaac")] == 3
                and marks[MARKS_ORDER.index("???")] == 3
                and marks[MARKS_ORDER.index("Satan")] == 3
                and marks[MARKS_ORDER.index("The Lamb")] == 3
            )
        else:
            mark_index = mark_indices[mark_name]
            completed = COMPLETION_MAP.get(
                str(completion_marks[character_name][mark_index]), False
            )

        completion_results.append(completed)

    return completion_results


def unify_results(challenges_df, normal_df, tainted_df):
    # Unify the results from all dataframes into a single dataframe
    # Shift to same scale as items unlocks
    challenges_df.columns = challenges_df.columns.str.strip()
    normal_df.columns = normal_df.columns.str.strip()
    tainted_df.columns = tainted_df.columns.str.strip()
    challenges_df["Reward"] = challenges_df["Reward"] - 1

    tainted_df["Character"] = tainted_df["Character"].apply(lambda x: f"Tainted {x}")

    # Concatenate all dataframes
    all_data = np.concat(
        [
            challenges_df[["Nº", "Name", "Reward", "Item", "Completed"]].values,
            normal_df.values,
            tainted_df.values,
        ],
        axis=0,
    )
    all_df = pd.DataFrame(
        all_data, columns=["Nº/Character", "Name/Mark", "Quality", "Item", "Completed"]
    )
    all_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    return all_df


def run_data_parser(save_data):
    # File paths
    challenges_tierlist_file = "src/data/challenges_data.csv"
    normal_unlocks_tierlist_file = "src/data/normal_characters_unlocks.csv"
    tainted_unlocks_tierlist_file = "src/data/tainted_characters_unlocks.csv"

    # Load CSV data
    challenges_tierlist_df = pd.read_csv(challenges_tierlist_file)
    normal_unlocks_tierlist_df = pd.read_csv(normal_unlocks_tierlist_file)
    tainted_unlocks_tierlist_df = pd.read_csv(tainted_unlocks_tierlist_file)

    # Read save file

    # Process challenges
    challenges_completed = get_challenges(save_data)
    challenges_tierlist_df["Completed"] = challenges_completed
    challenges_tierlist_df["Completed"] = challenges_tierlist_df["Completed"].astype(
        bool
    )

    # Process normal character completion marks
    normal_completions = process_normal_character_marks(
        save_data, normal_unlocks_tierlist_df
    )
    normal_unlocks_tierlist_df["Completed"] = normal_completions

    # Process tainted character completion marks
    tainted_completions = process_tainted_character_marks(
        save_data, tainted_unlocks_tierlist_df
    )
    tainted_unlocks_tierlist_df["Completed"] = tainted_completions

    # Unify results
    all_df = unify_results(
        challenges_tierlist_df, normal_unlocks_tierlist_df, tainted_unlocks_tierlist_df
    )

    return all_df


if __name__ == "__main__":
    with open(
        r"C:\Program Files (x86)\Steam\userdata\364981890\250900\remote\ab_persistentgamedata1.dat",
        "rb",
    ) as f:
        data = f.read()
    for i in range(36):
        print(i, get_checklist_unlocks(data, i))
