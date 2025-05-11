from flask import Flask, request, render_template, jsonify
import os
import sys

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.dr_lupo_analyzer import DrLupoAnalyzer

app = Flask(__name__)

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

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