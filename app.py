from flask import Flask, request, render_template, jsonify
import json
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.dr_lupo_analyzer import DrLupoAnalyzer

app = Flask(__name__)

CHALLENGES_DIR = Path(__file__).resolve().parent / "challenges"


@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')


@app.route('/play/<challenge_id>')
def play_challenge(challenge_id):
    """Serve the live scoring challenge page."""
    return render_template('challenge.html')


@app.route('/api/challenge/<challenge_id>')
def get_challenge(challenge_id):
    """Return pre-computed challenge JSON."""
    safe_name = "".join(c for c in challenge_id if c.isalnum() or c in ('_', '-'))
    path = CHALLENGES_DIR / f"{safe_name}.json"
    if not path.exists():
        return jsonify({"error": "Challenge not found"}), 404
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/challenges')
def list_challenges():
    """List available challenges."""
    if not CHALLENGES_DIR.exists():
        return jsonify([])
    challenges = []
    for p in sorted(CHALLENGES_DIR.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        challenges.append({
            "id": p.stem,
            "game_url": d.get("game_url"),
            "white": d.get("white"),
            "black": d.get("black"),
            "player_color": d.get("player_color"),
            "num_moves": d.get("num_moves"),
        })
    return jsonify(challenges)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a Lichess game for the Dr Lupo Challenge."""
    lichess_url = request.form.get('url')
    engine_depth = int(request.form.get('depth', 16))
    margin_cp = float(request.form.get('margin', 5))  # Changed default to 5cp
    
    if not lichess_url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Create an analyzer instance
    analyzer = DrLupoAnalyzer(
        engine_depth=engine_depth,
        margin_cp=margin_cp
    )
    
    # Analyze the game
    results = analyzer.analyze_game(lichess_url)
    
    if 'error' in results:
        return jsonify(results), 400
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))