import os

from Poker_parser import create_dataset
from Poker_analysis import analyze_complete


def main():

    PLURIBUS_PATH = 'pluribus'
    DATA_DIR = 'data'
    OUTPUT_DIR = 'outputs'

    # Only (re)parse when the raw .phh dataset is present. A fresh clone ships
    # the parsed output in data/, so by default we skip straight to analysis.
    # Run download_data.py to fetch pluribus/ and reprocess from scratch.
    if os.path.isdir(PLURIBUS_PATH) and any(os.scandir(PLURIBUS_PATH)):
        create_dataset(
            pluribus_path=PLURIBUS_PATH,
            output_dir=DATA_DIR
        )
    else:
        print(f"'{PLURIBUS_PATH}/' not found - using the committed parsed data in '{DATA_DIR}/'.")
        print("Run 'python download_data.py' first if you want to reprocess from the raw .phh files.\n")

    analysis = analyze_complete(
        hands_path=f'{DATA_DIR}/hands.parquet',
        players_path=f'{DATA_DIR}/players_in_hand.parquet',
        save_dir=OUTPUT_DIR
    )
    
    return analysis


if __name__ == "__main__":
    analysis = main()