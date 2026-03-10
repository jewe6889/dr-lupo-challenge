from flask import Flask, request, render_template, jsonify
import atexit
import json
import os
import sys
import threading
import time
from pathlib import Path

import chess
import chess.engine

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.dr_lupo_analyzer import DrLupoAnalyzer
from src.challenge_builder import find_stockfish

app = Flask(__name__)

BEST_MOVE_MARGIN_CP = 49

# ---- Stockfish engine lifecycle (singleton for Survival Mode) ----
_engine = None
_engine_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        engine_path = find_stockfish()
        _engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    return _engine

def restart_engine():
    """Kill and reopen the engine (call while holding _engine_lock)."""
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:
            pass
        _engine = None
    return get_engine()

def shutdown_engine():
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:
            pass
        _engine = None

atexit.register(shutdown_engine)

CHALLENGES_DIR = Path(__file__).resolve().parent / "challenges"


@app.route('/')
def home():
    """Render the main menu."""
    return render_template('menu.html')


@app.route('/play/<challenge_id>')
def play_challenge(challenge_id):
    """Serve the live scoring challenge page."""
    return render_template('challenge.html')


@app.route('/survival/<challenge_id>')
def survival_mode(challenge_id):
    """Serve the Survival Mode page."""
    return render_template('survival.html')


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


@app.route('/api/survival/analyze', methods=['POST'])
def survival_analyze():
    """On-demand Stockfish analysis for Survival Mode branching.

    Input JSON: {fen, player_move}  (player_move is UCI string)
    Returns: opponent best reply + full analysis of the resulting position.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    fen = data.get('fen')
    player_move = data.get('player_move')
    depth = data.get('depth', 18)

    if not fen or not player_move:
        return jsonify({"error": "fen and player_move are required"}), 400

    try:
        board = chess.Board(fen)
    except ValueError:
        return jsonify({"error": "Invalid FEN"}), 400

    move = chess.Move.from_uci(player_move)
    if move not in board.legal_moves:
        return jsonify({"error": "Illegal move"}), 400

    with _engine_lock:
      try:
        engine = get_engine()

        # 1. Push player's move
        board.push(move)
        fen_after_player = board.fen()

        # 2. Get opponent's best reply
        if board.is_game_over():
            return jsonify({
                "opponent_reply_uci": None,
                "opponent_reply_san": None,
                "fen_after_player": fen_after_player,
                "fen_after_opponent": fen_after_player,
                "game_over": True,
                "position": None,
            })

        result = engine.play(board, chess.engine.Limit(depth=depth))
        opp_move = result.move
        opp_san = board.san(opp_move)
        opp_uci = opp_move.uci()
        board.push(opp_move)
        fen_after_opponent = board.fen()

        # 3. Analyze all legal moves in the resulting position
        if board.is_game_over():
            return jsonify({
                "opponent_reply_uci": opp_uci,
                "opponent_reply_san": opp_san,
                "fen_after_player": fen_after_player,
                "fen_after_opponent": fen_after_opponent,
                "game_over": True,
                "position": None,
            })

        # Use multipv for efficient single-call analysis
        num_legal = len(list(board.legal_moves))
        infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=num_legal)

        all_moves = []
        for info in infos:
            mv = info["pv"][0]
            score_cp = info["score"].relative.score(mate_score=100000)
            all_moves.append({
                "uci": mv.uci(),
                "san": board.san(mv),
                "eval_cp": score_cp,
            })

        all_moves.sort(key=lambda x: x["eval_cp"], reverse=True)
        best_eval = all_moves[0]["eval_cp"]
        best_moves = [m for m in all_moves if (best_eval - m["eval_cp"]) <= BEST_MOVE_MARGIN_CP]

        position = {
            "fen": fen_after_opponent,
            "best_moves": [{"uci": m["uci"], "san": m["san"], "eval_cp": m["eval_cp"]} for m in best_moves[:3]],
            "all_moves": all_moves,
            "best_move_count": min(len(best_moves), 3),
        }

        return jsonify({
            "opponent_reply_uci": opp_uci,
            "opponent_reply_san": opp_san,
            "fen_after_player": fen_after_player,
            "fen_after_opponent": fen_after_opponent,
            "game_over": False,
            "position": position,
        })
      except chess.engine.EngineTerminatedError:
        engine = restart_engine()
        return jsonify({"error": "Engine crashed, please retry"}), 503
      except chess.engine.EngineError as e:
        return jsonify({"error": f"Engine error: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))