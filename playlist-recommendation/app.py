import os
import pickle
import pandas as pd
from tqdm import tqdm
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

PORT_API_REST = 52025
RULES_PATH = "../models"
FREQUENT_ITEMSETS_PATH = os.path.join(RULES_PATH, "frequent_itemsets.pkl")
RULES_PATH = os.path.join(RULES_PATH, "rules.pkl")

def load_rules():
    try:
        with open(RULES_PATH, "rb") as file:
            rules = pickle.load(file)
        return rules
    except:
        print(f"Unable to load rules for generating recommendations")
        return {"error": "Unable to load rules for generating recommendations."}

def recommend_music(artist_names, track_names, rules, df, top_n=5):
    recommendations = []
    artist_track_pairs = [f"{artist}|{track}" for artist, track in zip(artist_names, track_names)]

    for pair in artist_track_pairs:
        matching_rules = [rule for rule in rules if pair in rule[0]]
        if matching_rules:
            for rule in matching_rules:
                recommendations.extend(rule[1])
        else:
            recommendations = ['rihanna']

    recommendations = list(set(recommendations))[:top_n]
    return recommendations

def process_csv(music_csv):
    try:
        df = pd.read_csv(music_csv, sep=",")
        df['artist_track'] = df['artist_name'] + "|" + df['track_name']
        return df, df['artist_track'].tolist()

    except:
        print(f"Unable to load CSV file. It must be in the form artist_name, track_name")
        return {"error": "Unable to load CSV file."}


@app.route('/api/recommend', methods=['POST'])
def recommend_api():
    if 'file' not in request.files:
        return jsonify({"error": "CSV file not uploaded."}), 400

    csv_file = request.files['file']
    try:
        df, artist_tracks = process_csv(csv_file)
    except:
        error = process_csv(csv_file)

    rules = load_rules()

    if "error" in rules:
        return jsonify(rules), 400

    recommendations = recommend_music(artist_tracks, rules, df, top_n=5)
    if not recommendations:
        return jsonify({"error": "No recommendations were generated for the submitted songs."}), 404

    return jsonify({"recommendations": recommendations})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error="CSV file not uploaded.")

    csv_file = request.files['file']
    result = process_csv(csv_file)
    df, transactions = result

    rules = load_rules()

    if "error" in rules:
        return render_template('index.html', error=rules["error"])

    artist_names = df['artist_name'].tolist()
    track_names = df['track_name'].tolist()

    recommendations = recommend_music(artist_names, track_names, rules, df, top_n=5)

    if not recommendations:
        return render_template('index.html', error="No recommendations were generated for the submitted songs.")

    return render_template('index.html', recommendations=recommendations)


if __name__ == '__main__':
    app.run(debug=True, port=PORT_API_REST)
