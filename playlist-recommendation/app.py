import os
import pickle
from typing import List, Dict
from collections import defaultdict
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

PORT_API_REST = 52025
RULES_PATH = "../models"
RULES_FILE = os.path.join(RULES_PATH, "rules.pkl")
FREQUENT_ITEMSETS_PATH = os.path.join(RULES_PATH, "frequent_itemsets.pkl")

def load_rules():
    """Load recommendation rules from pickle."""
    try:
        with open(RULES_FILE, "rb") as file:
            rules = pickle.load(file)
        return rules
    except:
        print(f"Unable to load rules")
        return {"error": "Unable to load rules for generating recommendations."}

def load_frequent_itemsets():
    """Load frequent itemsets from pickle."""
    try:
        with open(FREQUENT_ITEMSETS_PATH, "rb") as file:
            frequent_itemsets = pickle.load(file)
        return frequent_itemsets
    except:
        print(f"Unable to load frequent itemsets")
        return []

def generate_popular_songs_from_itemsets(frequent_itemsets: List[set], top_n: int = 10) -> List[str]:
    """Generate a list of popular songs from frequent itemsets."""
    item_support = defaultdict(int)

    for itemset in frequent_itemsets:
        for item in itemset:
            item_support[item] += 1
    sorted_items = sorted(item_support.items(), key=lambda x: x[1], reverse=True)
    popular_songs = [item for item, _ in sorted_items[:top_n]]
    return popular_songs
    
def recommend_music(track_names: List[str], rules, popular_songs: List[str], top_n=5):
    """Generate music recommendations based on track names."""
    recommendations = []

    for track in track_names:
        matching_rules = [rule for rule in rules if track in rule[0]]
        if matching_rules:
            for rule in matching_rules:
                recommendations.extend(rule[1])
        else:
            recommendations.extend(popular_songs)

    recommendations = list(set(recommendations))[:top_n]
    return recommendations


@app.route('/api/recommend', methods=['POST'])
def recommend_api():
    """endpoint recommendation."""

    data = request.get_json()
    if not data or 'songs' not in data:
        return jsonify({"error": "Invalid JSON or missing 'songs' field"}), 400

    track_names = data['songs']
    rules = load_rules()
    if "error" in rules:
        return jsonify(rules), 400

    frequent_itemsets = load_frequent_itemsets()
    if frequent_itemsets:
        popular_songs = generate_popular_songs_from_itemsets(frequent_itemsets, top_n=10)
    else:
        popular_songs = ["Umbrella - Rihanna", "Diamonds - Rihanna"]

    recommendations = recommend_music(track_names, rules, popular_songs, top_n=5)
    if not recommendations:
        return jsonify({"error": "No recommendations were generated for the submitted songs."}), 404

    return jsonify({"recommendations": recommendations})

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=PORT_API_REST)