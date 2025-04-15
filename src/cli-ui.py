import argparse
import ObtainData


def read_save_file(filename):
    """Read binary data from save file."""
    with open(filename, "rb") as f:
        return f.read()


def main():

    parser = argparse.ArgumentParser(description="CLI for the application")

    parser.add_argument(
        "-f", "--file", type=str, help="Path to the file to be processed", required=True
    )

    file_path = parser.parse_args().file
    save_data = read_save_file(file_path)

    all_df = ObtainData.run_data_parser(save_data)

    # Here are some examples in which you can sort the data
    # # Sort by quality (bets to worst)
    # all_df = all_df.sort_values(by="Quality", ascending=False)

    # # Sort by quality and completed (show first not completed)
    all_df = all_df.sort_values(by=["Completed", "Quality"], ascending=[True,False])

    print("""
          #######################################################
          # The Binding of Isaac: Repentance Completion Tracker #
          #######################################################
          """)
    
    print("Showing first 20 entries:")
    print("\n")

    print(all_df.head(20))


if __name__ == "__main__":
    main()
