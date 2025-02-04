import os
import pickle
import pandas as pd
from tqdm import tqdm
from fpgrowth_py import fpgrowth
from typing import List, Tuple, Set, Any

DATA_PATH = "/home/giuliacastro/project2-pv2/data"
#CSV_PATH = os.path.join(DATA_PATH, "2023_spotify_ds1.csv")
RULES_PATH = "/home/giuliacastro/project2-pv2/rules"
FREQUENT_ITEMSETS_PATH = os.path.join(RULES_PATH, "frequent_itemsets.pkl")
RULES_PATH = os.path.join(RULES_PATH, "rules.pkl")

def get_latest_csv(data_path:str) -> str:
    """
    Fetch the latest CSV file from PersistentVolumeClaim.
    Args:
        data_path (str): Location to fetch the latest dataset.
    """
    files = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        raise FileNotFoundError("No datasets were found for association rule generation")
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def recommend_artist_track(artist_track:str, rules:List[Tuple[Set[str], Set[str]]], rec_num:int=5) -> List[str]:
    """
    Recommends artists or tracks based on generated association rules.
    Args:
        artist_track (str): Artist or track to generate recommendations.
        rules (List): Association rules generated using the FP-Growth algorithm.
        rec_num: Number of recommendations.
    """
    recommendations = [
        rule[1]
        for rule in rules
        if artist_track in rule[0]
    ]
    flat_recommendations = [item for sublist in recommendations for item in sublist]
    return list(set(flat_recommendations))[:rec_num]


def evaluate_recommendations(rules: List[Tuple[Set[str], Set[str]]], transactions: List[List[str]]) -> None:
    """
    Evaluates recommendations based on coverage.
    Args:
        rules (List): Association rules generated using the FP-Growth algorithm.
        transactions (List): Transactions grouped by playlist.
    """
    covered_items = set(item for rule in rules for item in rule[1])
    all_items = set(item for transaction in transactions for item in transaction)
    coverage = len(covered_items.intersection(all_items))/len(all_items)
    print(f"Coverage: {coverage:.2%}")

def generate_transactions(df: pd.DataFrame) -> List[List[str]]:
    """
    Generates transactions by grouping artists and track by playlist.
    Args:
        df (pd.DataFrame): DataFrame with playlist information.
    """
    transactions = []
    for pid, group in df.groupby('pid'):
        transaction = group['track_name'].tolist()
        transactions.append(transaction)
    
    return transactions


if __name__ == "__main__":
    csv_path = get_latest_csv(DATA_PATH)
    df_rec = pd.read_csv(csv_path)
    transactions = generate_transactions(df_rec)

    with tqdm(total=1, desc="FP-Growth Processing", dynamic_ncols=True) as pbar:
        frequent_itemsets, rules = fpgrowth(
        transactions,
        minSupRatio=0.05,
        minConf=0.7,
        )
        pbar.update(1)
    print(f"Total rules generated: {len(rules)}")

    evaluate_recommendations(rules, transactions)

    with open(FREQUENT_ITEMSETS_PATH, "wb") as f:
        pickle.dump(frequent_itemsets, f)
    with open(RULES_PATH, "wb") as f:
        pickle.dump(rules, f)
