from Poker_parser import create_dataset
from Poker_analysis import analyze_complete


def main():

    PLURIBUS_PATH = 'pluribus'
    DATA_DIR = 'data'
    OUTPUT_DIR = 'outputs'
   

    create_dataset(
        pluribus_path=PLURIBUS_PATH,
        output_dir=DATA_DIR
    )

    analysis = analyze_complete(
        hands_path=f'{DATA_DIR}/hands.parquet',
        players_path=f'{DATA_DIR}/players_in_hand.parquet',
        save_dir=OUTPUT_DIR
    )
    
    return analysis


if __name__ == "__main__":
    analysis = main()