#!/usr/bin/env python3
"""
Challenge Builder — Pre-analyzes a Lichess game for the Dr Lupo Live Scoring Challenge.

For each of the 26 positions (player's color), runs Stockfish on every legal move
and classifies "best moves" within 49cp of the top eval.

Usage:
    python -m src.challenge_builder https://lichess.org/mfJW36UO#14
    python -m src.challenge_builder https://lichess.org/mfJW36UO#14 --depth 18 --engine path/to/stockfish
"""

import argparse
import json
import re
import sys
import time
from io import StringIO
from pathlib import Path

import chess
import chess.engine
import chess.pgn
import requests

BEST_MOVE_MARGIN_CP = 49  # Moves within 49cp of the best are "best moves"


def find_stockfish():
    paths = [
        "stockfish",
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/bin/stockfish",
        "/opt/homebrew/bin/stockfish",
        str(Path.home() / "stockfish" / "stockfish"),
    ]
    # Windows-specific common paths
    for p in Path.home().glob("**/stockfish*.exe"):
        paths.insert(0, str(p))
        break
    for path in paths:
        if Path(path).exists():
            return path
    return "stockfish"


def fetch_game(url: str):
    """Fetch game PGN from Lichess and parse the start ply from the URL."""
    m = re.search(r"lichess\.org/([a-zA-Z0-9]{8})", url)
    if not m:
        raise ValueError("Invalid Lichess URL")
    game_id = m.group(1)

    ply_match = re.search(r"#(\d+)", url)
    start_ply = int(ply_match.group(1)) if ply_match else 0

    api_url = f"https://lichess.org/game/export/{game_id}?evals=false&clocks=false"
    resp = requests.get(api_url, headers={"Accept": "application/x-chess-pgn"}, timeout=15)
    if resp.status_code != 200:
        raise ValueError(f"Lichess API returned {resp.status_code}")

    game = chess.pgn.read_game(StringIO(resp.text))
    if not game:
        raise ValueError("Could not parse PGN")

    return game_id, game, start_ply


def build_challenge(game_id, game, start_ply, engine_path, depth, num_moves=26):
    """Analyze 26 positions for the player's color and return challenge JSON."""

    # Walk to the start ply to determine player color and collect the mainline
    board = chess.Board()
    mainline_moves = list(game.mainline_moves())

    if start_ply > len(mainline_moves):
        raise ValueError(f"Start ply {start_ply} exceeds game length {len(mainline_moves)}")

    # Advance to the start position
    for i in range(start_ply):
        board.push(mainline_moves[i])

    # Who is to move at start_ply? That's the player's color.
    player_color = board.turn  # chess.WHITE or chess.BLACK
    color_name = "white" if player_color == chess.WHITE else "black"
    print(f"Player color: {color_name} (to move at ply {start_ply})")
    print(f"Starting FEN: {board.fen()}")

    # Collect the positions that the player needs to play from.
    # From start_ply onward, every other ply is the player's move.
    # We need 26 player-moves and the opponent replies after each.
    positions_data = []
    ply_cursor = start_ply

    remaining = mainline_moves[start_ply:]

    # remaining[0] is the player's move, [1] is opponent's reply, [2] is player's next, etc.
    player_move_indices = list(range(0, len(remaining), 2))  # 0, 2, 4, ...

    if len(player_move_indices) < num_moves:
        print(f"Warning: only {len(player_move_indices)} player moves available (wanted {num_moves})")
        num_moves = len(player_move_indices)

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    try:
        for pos_idx in range(num_moves):
            pm_idx = player_move_indices[pos_idx]
            # Board is at the position *before* the player's move
            fen_before = board.fen()
            played_move = remaining[pm_idx]

            legal_moves = list(board.legal_moves)
            total = len(legal_moves)
            move_num_display = pos_idx + 1
            full_move = board.fullmove_number
            side = "W" if board.turn == chess.WHITE else "B"
            print(f"\n[{move_num_display}/{num_moves}] Analyzing position (move {full_move}{side}): {total} legal moves ...")

            # Analyze every legal move
            all_moves = []
            t0 = time.time()
            for j, mv in enumerate(legal_moves):
                board.push(mv)
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                # Score is from the perspective of the side that just moved (player),
                # but engine reports from the side-to-move perspective. Negate it.
                raw_score = info["score"].relative.score(mate_score=100000)
                eval_cp = -raw_score  # negate: positive = good for the player
                board.pop()
                all_moves.append({
                    "uci": mv.uci(),
                    "san": board.san(mv),
                    "eval_cp": eval_cp,
                })

            elapsed = time.time() - t0
            # Sort: best for the player first (highest eval)
            all_moves.sort(key=lambda x: x["eval_cp"], reverse=True)

            best_eval = all_moves[0]["eval_cp"]
            best_moves = [m for m in all_moves if (best_eval - m["eval_cp"]) <= BEST_MOVE_MARGIN_CP]
            best_count = len(best_moves)
            # Cap display at 3
            display_count = min(best_count, 3)

            played_san = board.san(played_move)
            played_among_best = any(m["uci"] == played_move.uci() for m in best_moves)
            print(f"  {elapsed:.1f}s — best eval: {best_eval}cp, "
                  f"best moves (within {BEST_MOVE_MARGIN_CP}cp): {best_count}, "
                  f"played: {played_san} {'✅' if played_among_best else '❌'}")
            for bm in best_moves[:5]:
                marker = " ← played" if bm["san"] == played_san else ""
                print(f"    {bm['san']:>8} {bm['eval_cp']:>+6}cp{marker}")

            # Get opponent's reply (if it exists)
            opp_reply_idx = pm_idx + 1
            opponent_reply_uci = None
            opponent_reply_san = None
            fen_after_opponent = None

            # Push the actually-played move to advance the board
            board.push(played_move)
            fen_after_game_move = board.fen()  # position after player's game move, before opponent reply

            if opp_reply_idx < len(remaining):
                opp_move = remaining[opp_reply_idx]
                opponent_reply_san = board.san(opp_move)
                opponent_reply_uci = opp_move.uci()
                board.push(opp_move)
                fen_after_opponent = board.fen()
            else:
                fen_after_opponent = board.fen()

            positions_data.append({
                "move_number": move_num_display,
                "fen": fen_before,
                "game_move_san": played_san,
                "game_move_uci": played_move.uci(),
                "best_moves": [{"uci": m["uci"], "san": m["san"], "eval_cp": m["eval_cp"]} for m in best_moves],
                "best_move_count": display_count,
                "all_moves": all_moves,
                "fen_after_game_move": fen_after_game_move,
                "opponent_reply_uci": opponent_reply_uci,
                "opponent_reply_san": opponent_reply_san,
                "fen_after_opponent": fen_after_opponent,
            })
    finally:
        engine.quit()

    # Build game metadata
    white_player = game.headers.get("White", "?")
    black_player = game.headers.get("Black", "?")
    game_url = f"https://lichess.org/{game_id}"

    # Compute the real player's score using the same scoring rules
    real_player_score = 0
    real_player_best_count = 0
    for pos in positions_data:
        gm_uci = pos["game_move_uci"]
        best_ucis = [m["uci"] for m in pos["best_moves"]]
        best_eval = pos["best_moves"][0]["eval_cp"]
        if gm_uci in best_ucis:
            real_player_score += 3
            real_player_best_count += 1
        else:
            gm_eval = next((m["eval_cp"] for m in pos["all_moves"] if m["uci"] == gm_uci), 0)
            penalty = max(0, best_eval - gm_eval) / 100
            real_player_score -= penalty

    challenge = {
        "game_id": game_id,
        "game_url": game_url,
        "white": white_player,
        "black": black_player,
        "white_title": game.headers.get("WhiteTitle", ""),
        "black_title": game.headers.get("BlackTitle", ""),
        "white_elo": game.headers.get("WhiteElo", ""),
        "black_elo": game.headers.get("BlackElo", ""),
        "event": game.headers.get("Event", ""),
        "time_control": game.headers.get("TimeControl", ""),
        "start_ply": start_ply,
        "player_color": color_name,
        "num_moves": num_moves,
        "engine_depth": depth,
        "margin_cp": BEST_MOVE_MARGIN_CP,
        "real_player_score": round(real_player_score, 2),
        "real_player_best_count": real_player_best_count,
        "positions": positions_data,
    }
    return challenge


def main():
    parser = argparse.ArgumentParser(description="Build a Dr Lupo Live Scoring challenge from a Lichess game")
    parser.add_argument("url", help="Lichess game URL (with optional #ply)")
    parser.add_argument("--depth", type=int, default=18, help="Stockfish depth (default: 18)")
    parser.add_argument("--engine", default=None, help="Path to Stockfish binary")
    parser.add_argument("--moves", type=int, default=26, help="Number of player moves to analyze (default: 26)")
    parser.add_argument("--output", default=None, help="Output JSON path (default: challenges/<id>_ply<N>.json)")
    args = parser.parse_args()

    engine_path = args.engine or find_stockfish()
    print(f"Using engine: {engine_path}")
    print(f"Depth: {args.depth}")

    game_id, game, start_ply = fetch_game(args.url)
    print(f"Game: {game_id}, start ply: {start_ply}")

    challenge = build_challenge(game_id, game, start_ply, engine_path, args.depth, args.moves)

    out_dir = Path(__file__).resolve().parent.parent / "challenges"
    out_dir.mkdir(exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / f"{game_id}_ply{start_ply}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(challenge, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Challenge saved to {out_path}")
    print(f"   {challenge['num_moves']} positions, {challenge['player_color']} to play")


if __name__ == "__main__":
    main()
