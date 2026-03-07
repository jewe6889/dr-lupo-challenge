#!/usr/bin/env python3
"""
Dr Lupo Challenge Analyzer

Analyzes a Lichess game to determine if the player has completed the Dr Lupo Challenge:
1. Sacrifice your queen within the first 10 moves
2. Follow with 26 consecutive best engine moves
"""

import argparse
import re
import sys
import time
from pathlib import Path
from io import StringIO

import chess
import chess.engine
import chess.pgn
import requests


class DrLupoAnalyzer:
    """Analyzer for the Dr Lupo Challenge."""

    def __init__(self, engine_path=None, engine_depth=16, margin_cp=25):
        """
        Initialize the analyzer.
        
        Args:
            engine_path: Path to Stockfish engine. If None, will try to find it.
            engine_depth: Engine analysis depth.
            margin_cp: Margin of error in centipawns (default: 25).
        """
        self.engine_path = engine_path or self._find_stockfish()
        self.engine_depth = engine_depth
        self.margin_cp = margin_cp  # Already in centipawns
        self.engine = None
    
    def _find_stockfish(self):
        """Try to find Stockfish on the system."""
        # Common paths for Stockfish
        paths = [
            "/usr/games/stockfish",
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
            str(Path.home() / "stockfish" / "stockfish"),
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        # If we can't find Stockfish, return the command name and hope it's in PATH
        return "stockfish"
    
    def _extract_game_id(self, url):
        """Extract Lichess game ID from URL."""
        match = re.search(r"lichess\.org/([a-zA-Z0-9]{8})", url)
        if not match:
            raise ValueError("Invalid Lichess URL. Expected format: https://lichess.org/XXXXXXXX")
        return match.group(1)
    
    def _fetch_game_pgn(self, game_id):
        """Fetch game PGN from Lichess API."""
        url = f"https://lichess.org/game/export/{game_id}?evals=false&clocks=false"
        headers = {"Accept": "application/x-chess-pgn"}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch game: {response.status_code}")
        
        return response.text
    
    def _detect_queen_sacrifice(self, game, max_move=10):
        """
        Detect the first queen sacrifice within the first 10 moves.
        
        Returns:
            tuple: (queen_sacrificed, player_color, move_number, position_fen, sacrifice_move_san)
            or (False, None, None, None, None) if no sacrifice was found.
        """
        board = chess.Board()
        white_has_queen = True
        black_has_queen = True
        current_move = 1
        
        # Check initial position for queens (handles chess variants)
        white_queen_present = any(board.piece_at(sq) == chess.Piece(chess.QUEEN, chess.WHITE) 
                                for sq in chess.SQUARES)
        black_queen_present = any(board.piece_at(sq) == chess.Piece(chess.QUEEN, chess.BLACK) 
                                for sq in chess.SQUARES)
        
        for node in game.mainline():
            move = node.move
            
            # Check if the move is a capture of a queen
            if board.piece_at(move.to_square) is not None and board.piece_at(move.to_square).piece_type == chess.QUEEN:
                captured_piece = board.piece_at(move.to_square)
                
                # White's queen captured → White sacrificed their queen
                if captured_piece.color == chess.WHITE and white_queen_present:
                    white_has_queen = False
                    sacrifice_move_san = board.san(move)
                    board.push(move)
                    return True, chess.WHITE, current_move, board.fen(), sacrifice_move_san
                
                # Black's queen captured → Black sacrificed their queen
                elif captured_piece.color == chess.BLACK and black_queen_present:
                    black_has_queen = False
                    sacrifice_move_san = board.san(move)
                    board.push(move)
                    return True, chess.BLACK, current_move, board.fen(), sacrifice_move_san
            
            # Make the move on our board
            board.push(move)
            
            # Update move counter (increment after White's move)
            if board.turn == chess.WHITE:
                current_move += 1
            
            # Stop if we've gone past the max move limit
            if current_move > max_move:
                break
        
        return False, None, None, None, None
    
    def _analyze_move(self, board, played_move):
        """
        Analyze a position and determine if the played move was the best move.
        
        Args:
            board: Chess position to analyze
            played_move: The move that was played
            
        Returns:
            tuple: (is_best, best_move, score_diff, played_move_rank, all_top_moves)
        """
        # Get the top moves from the engine
        result = self.engine.analyse(
            board, 
            chess.engine.Limit(depth=self.engine_depth),
            multipv=5  # Get top 5 moves for better context
        )
        
        # Get the best move and its score
        best_move = result[0]["pv"][0]
        best_score = result[0]["score"].relative.score(mate_score=10000)
        
        # Find the evaluation and rank of the played move
        played_score = None
        played_move_rank = None
        all_top_moves = []
        
        for i, analysis in enumerate(result):
            move = analysis["pv"][0]
            score = analysis["score"].relative.score(mate_score=10000)
            move_san = board.san(move)
            
            all_top_moves.append({
                "move": move_san,
                "score": score,
                "rank": i + 1
            })
            
            if move == played_move:
                played_score = score
                played_move_rank = i + 1
        
        # If we couldn't find the played move in the top moves, analyze it directly
        if played_score is None:
            board_copy = board.copy()
            board_copy.push(played_move)
            played_result = self.engine.analyse(
                board_copy,
                chess.engine.Limit(depth=self.engine_depth)
            )
            played_score = -played_result["score"].relative.score(mate_score=10000)
            played_move_rank = len(result) + 1  # Rank it below the analyzed top moves
            
            # Add the played move to the list
            all_top_moves.append({
                "move": board.san(played_move),
                "score": played_score,
                "rank": played_move_rank
            })
        
        # Calculate the difference in centipawns
        score_diff = best_score - played_score if played_score is not None else float('inf')
        
        # Check if the move is within margin of error
        is_best = abs(score_diff) <= self.margin_cp
        
        return is_best, best_move, score_diff, played_move_rank, all_top_moves
    
    def analyze_moves_after_sacrifice(self, game, player_color, start_move):
        """
        Analyze the 26 moves after the queen sacrifice.
        
        Args:
            game: Chess game
            player_color: Color of the player who sacrificed their queen
            start_move: Move number to start analysis from
            
        Returns:
            dict: Analysis results
        """
        # Start fresh with a new board
        board = chess.Board()
        move_count = 0
        best_move_count = 0
        current_streak = 0
        max_streak = 0
        analysis_results = []
        current_move = 1
        sacrifice_reached = False
        moves_to_analyze = 26
        
        # Initialize the engine
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        
        try:
            # Play through the game and analyze after the sacrifice
            for node in game.mainline():
                # Get the move
                move = node.move
                
                # Check if the move is legal
                if not move in board.legal_moves:
                    print(f"Warning: Illegal move {board.san(move)} in position {board.fen()}")
                    continue
                
                # Make the move on our board
                board.push(move)
                
                # Update move counter (increment after White's move)
                if board.turn == chess.WHITE:
                    current_move += 1
                
                # Skip past the sacrifice move (use > to exclude the sacrifice itself)
                if current_move > start_move and not sacrifice_reached:
                    sacrifice_reached = True
                    continue
                
                # Analyze moves BY the player who sacrificed (board.turn != player means player just moved)
                if sacrifice_reached and board.turn != player_color:
                    # Before the player's next move, check if we should analyze their previous move
                    if move_count < moves_to_analyze:
                        # Get the position before the player's move
                        prev_board = board.copy()
                        prev_board.pop()  # Remove the last move
                        
                        # Find the move the player made and analyze it
                        for legal_move in prev_board.legal_moves:
                            if legal_move == move:
                                is_best, best_move, score_diff, move_rank, top_moves = self._analyze_move(prev_board, move)
                                
                                # Track stats
                                if is_best:
                                    best_move_count += 1
                                    current_streak += 1
                                    max_streak = max(max_streak, current_streak)
                                else:
                                    current_streak = 0
                                
                                # Save analysis with detailed move info
                                analysis_results.append({
                                    "move_number": prev_board.fullmove_number,
                                    "move": prev_board.san(move),
                                    "is_best": is_best,
                                    "best_move": prev_board.san(best_move) if best_move else None,
                                    "score_diff": score_diff,
                                    "move_rank": move_rank,
                                    "top_moves": top_moves
                                })
                                
                                move_count += 1
                                break
                
                # Check if the game ended prematurely
                if board.is_game_over():
                    break
                
                # Stop if we've analyzed enough moves
                if move_count >= moves_to_analyze:
                    break
            
            # Calculate accuracy
            accuracy = (best_move_count / min(move_count, moves_to_analyze)) * 100 if move_count > 0 else 0
            
            # Check if the challenge was completed
            challenge_completed = best_move_count == moves_to_analyze and move_count >= moves_to_analyze
            
            return {
                "challenge_completed": challenge_completed,
                "accuracy": accuracy,
                "best_moves": best_move_count,
                "total_moves_analyzed": move_count,
                "max_consecutive_best": max_streak,
                "move_analysis": analysis_results
            }
            
        finally:
            # Always close the engine
            if self.engine:
                self.engine.quit()
                self.engine = None
    
    def analyze_game(self, lichess_url):
        """
        Analyze a Lichess game for the Dr Lupo Challenge.
        
        Args:
            lichess_url: URL to a Lichess game
            
        Returns:
            dict: Analysis results
        """
        try:
            # Extract game ID and fetch PGN
            game_id = self._extract_game_id(lichess_url)
            pgn_text = self._fetch_game_pgn(game_id)
            
            # Parse the PGN
            game = chess.pgn.read_game(StringIO(pgn_text))  # Use StringIO from io module
            if not game:
                return {"error": "Failed to parse game PGN"}
            
            # Extract game metadata
            headers = dict(game.headers)
            
            # Detect queen sacrifice
            sacrifice_found, player_color, move_number, position_fen, sacrifice_move_san = (
                self._detect_queen_sacrifice(game)
            )
            
            if not sacrifice_found:
                return {
                    "game_url": lichess_url,
                    "game_id": game_id,
                    "white": headers.get("White", "Unknown"),
                    "black": headers.get("Black", "Unknown"),
                    "queen_sacrificed": False,
                    "error": "No queen sacrifice found in the first 10 moves."
                }
            
            # Analyze moves after sacrifice
            analysis = self.analyze_moves_after_sacrifice(
                game, player_color, move_number
            )
            
            # Prepare the result
            player_name = headers.get("White", "Unknown") if player_color == chess.WHITE else headers.get("Black", "Unknown")
            
            return {
                "game_url": lichess_url,
                "game_id": game_id,
                "white": headers.get("White", "Unknown"),
                "black": headers.get("Black", "Unknown"),
                "player": player_name,
                "queen_sacrificed": True,
                "sacrifice_move": move_number,
                "sacrifice_position_fen": position_fen,
                "sacrifice_move_san": sacrifice_move_san,
                "player_color": "white" if player_color == chess.WHITE else "black",
                **analysis
            }
            
        except Exception as e:
            return {"error": str(e)}


# --- Dr Lupo Challenge v2: Badges, Visuals, Graph ---

LUPO_TIERS = [
    (26, "Dr Lupo", "👑"),
    (20, "Master Lupo", "🟠"),
    (13, "Half Lupo", "🟡"),
    (7, "Prodigy Lupo", "🟢"),
    (5, "Padawan Lupo", "🔵"),
    (3, "Baby Lupo", "🍼"),
]


def determine_badge(max_streak):
    """Determine the highest badge earned based on max consecutive best moves."""
    for threshold, name, emoji in LUPO_TIERS:
        if max_streak >= threshold:
            return {"name": name, "emoji": emoji, "threshold": threshold}
    return {"name": "No Badge Yet", "emoji": "💀", "threshold": 0}


def next_badge(max_streak):
    """Determine the next badge to aim for."""
    for threshold, name, emoji in reversed(LUPO_TIERS):
        if max_streak < threshold:
            return {"name": name, "emoji": emoji, "threshold": threshold}
    return None


def generate_graph(results, output_path="dr_lupo_analysis.png", margin_cp=5):
    """Generate a visual analysis graph with move ranks and eval diffs."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        print("matplotlib not installed. Skipping graph generation.")
        print("Install with: python -m pip install matplotlib")
        return None

    moves = results["move_analysis"]
    if not moves:
        return None

    move_labels = [f"{m['move_number']}.{m['move']}" for m in moves]
    ranks = [m["move_rank"] for m in moves]
    eval_diffs = [abs(m["score_diff"]) for m in moves]
    is_best = [m["is_best"] for m in moves]

    colors = ["#2ecc71" if b else "#e74c3c" for b in is_best]

    fig, ax1 = plt.subplots(figsize=(max(14, len(moves) * 0.6), 7))

    # Dark theme
    fig.patch.set_facecolor('#1a1a2e')
    ax1.set_facecolor('#16213e')

    x = np.arange(len(moves))

    # Bars for move rank
    bars = ax1.bar(x, ranks, color=colors, alpha=0.85, width=0.7,
                   edgecolor='white', linewidth=0.5)
    ax1.set_ylabel("Move Rank (1 = best)", color='white', fontsize=12)
    ax1.set_xlabel("Moves after queen sacrifice", color='white', fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(move_labels, color='white', fontsize=7, rotation=55, ha='right')
    ax1.tick_params(axis='y', colors='white')
    ax1.set_ylim(0, max(ranks) + 1)
    ax1.invert_yaxis()

    # Add rank number on each bar
    for i, (bar, rank) in enumerate(zip(bars, ranks)):
        ax1.text(bar.get_x() + bar.get_width() / 2, rank + 0.15,
                 f"#{rank}", ha='center', va='top', fontsize=7,
                 color='white', fontweight='bold')

    # Eval diff line on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(x, eval_diffs, color='#f39c12', linewidth=2, marker='o',
             markersize=5, alpha=0.9, zorder=5)
    ax2.set_ylabel("Eval Difference (centipawns)", color='#f39c12', fontsize=12)
    ax2.tick_params(axis='y', colors='#f39c12')
    ax2.set_ylim(bottom=0)

    # Tolerance zone: green shaded area on eval diff axis
    ax2.axhspan(0, margin_cp, alpha=0.15, color='#2ecc71', zorder=0)
    ax2.axhline(y=margin_cp, color='#2ecc71', linewidth=1.5, linestyle='--', alpha=0.7)
    ax2.text(len(moves) - 0.5, margin_cp + 1, f'Tolerance: {margin_cp}cp',
             color='#2ecc71', fontsize=9, ha='right', va='bottom', fontstyle='italic')

    # Highlight best streaks with background shading
    streak_start = None
    for i, b in enumerate(is_best):
        if b and streak_start is None:
            streak_start = i
        elif not b and streak_start is not None:
            if i - streak_start >= 2:
                ax1.axvspan(streak_start - 0.4, i - 0.6, alpha=0.1,
                           color='#2ecc71', zorder=0)
            streak_start = None
    if streak_start is not None and len(is_best) - streak_start >= 2:
        ax1.axvspan(streak_start - 0.4, len(is_best) - 0.6, alpha=0.1,
                   color='#2ecc71', zorder=0)

    # Title with badge
    badge = determine_badge(results["max_consecutive_best"])
    title = f"Dr Lupo Challenge v2 -- {badge['name']}\n"
    title += f"Accuracy: {results['accuracy']:.1f}% ({results['best_moves']}/{results['total_moves_analyzed']}) "
    title += f"| Best streak: {results['max_consecutive_best']} "
    title += f"| {'COMPLETED' if results['challenge_completed'] else 'Not completed'}"
    ax1.set_title(title, color='white', fontsize=13, fontweight='bold', pad=20)

    # Legend
    best_patch = mpatches.Patch(color='#2ecc71', label='Best move')
    notbest_patch = mpatches.Patch(color='#e74c3c', label='Not best move')
    eval_line = plt.Line2D([0], [0], color='#f39c12', marker='o', label='Eval diff (cp)')
    tolerance_patch = mpatches.Patch(color='#2ecc71', alpha=0.3, label=f'Tolerance zone ({margin_cp}cp)')
    ax1.legend(handles=[best_patch, notbest_patch, eval_line, tolerance_patch], loc='lower left',
               facecolor='#16213e', edgecolor='white', labelcolor='white', fontsize=9)

    # Grid
    ax1.grid(axis='y', alpha=0.15, color='white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()

    return output_path


def print_visual_results(results, elapsed_time, show_verbose=False):
    """Print rich visual results to the terminal."""
    try:
        from colorama import init, Fore, Style
        init()
        G = Fore.GREEN; R = Fore.RED; Y = Fore.YELLOW; C = Fore.CYAN
        M = Fore.MAGENTA; W = Fore.WHITE; DIM = Style.DIM; RST = Style.RESET_ALL
        BOLD = Style.BRIGHT
    except ImportError:
        G = R = Y = C = M = W = DIM = RST = BOLD = ""

    line = f"{DIM}{'─' * 62}{RST}"

    print(f"\n{BOLD}{C}🎮  DR LUPO CHALLENGE v2  👑{RST}")
    print(line)

    # Game info
    print(f"{W}  Game:    {BOLD}{results['white']} vs {results['black']}{RST}")
    print(f"{W}  Link:    {C}{results['game_url']}{RST}")
    print(f"{W}  Player:  {BOLD}{results['player']} ({results['player_color']}){RST}")
    print(line)

    # Queen sacrifice
    if results["queen_sacrificed"]:
        sac_san = results.get("sacrifice_move_san", "?")
        print(f"{Y}  👑 QUEEN SACRIFICE{RST}")
        print(f"{W}  Move {results['sacrifice_move']} · {results['player_color'].title()} gave up the queen ({sac_san}){RST}")
        print(f"{DIM}  FEN: {results['sacrifice_position_fen']}{RST}")
        print(line)

    # Challenge results
    accuracy = results["accuracy"]
    best = results["best_moves"]
    total = results["total_moves_analyzed"]
    streak = results["max_consecutive_best"]
    completed = results["challenge_completed"]

    accuracy_color = G if accuracy >= 80 else Y if accuracy >= 50 else R
    streak_color = G if streak >= 7 else Y if streak >= 3 else R

    margin = results.get('margin_cp', 5)
    print(f"{BOLD}{M}  📊 CHALLENGE RESULTS{RST}")
    print(f"{W}  Accuracy:     {accuracy_color}{BOLD}{accuracy:.1f}%{RST} ({best}/{total} best moves)")
    print(f"{W}  Best streak:  {streak_color}{BOLD}{streak} consecutive best moves{RST}")
    print(f"{W}  Engine depth: {results.get('engine_depth', 16)}{RST}")
    print(f"{W}  Tolerance:    {G}{margin}cp{RST} {DIM}(moves within {margin}cp of best count as best){RST}")
    print(f"{W}  Completed:    {G}{BOLD}✅ YES{RST}" if completed else f"{W}  Completed:    {R}{BOLD}❌ NO{RST}")
    print()

    # Badge
    badge = determine_badge(streak)
    nxt = next_badge(streak)
    print(f"  {BOLD}🏆 BADGE: {badge['emoji']}  {badge['name']}{RST}", end="")
    if badge["threshold"] > 0:
        print(f"  {DIM}(streak ≥ {badge['threshold']}){RST}")
    else:
        print()
    if nxt:
        remaining = nxt["threshold"] - streak
        print(f"  {DIM}   Next: {nxt['emoji']}  {nxt['name']} — need {remaining} more consecutive best moves{RST}")
    print()

    # Wordle-style grid
    grid = f"  {Y}🟨{RST}"  # Queen sacrifice marker
    for m in results["move_analysis"]:
        grid += f"{G}🟩{RST}" if m["is_best"] else f"{R}🟥{RST}"
    print(f"  {BOLD}Move grid:{RST}")
    # Print in rows of 9
    moves_grid = [f"{Y}🟨{RST}"] + [f"{G}🟩{RST}" if m["is_best"] else f"{R}🟥{RST}" for m in results["move_analysis"]]
    row_size = 9
    for i in range(0, len(moves_grid), row_size):
        print(f"  {''.join(moves_grid[i:i+row_size])}")
    print(f"  {DIM}🟨=Queen sac  🟩=Best move  🟥=Not best{RST}")
    print(line)

    # Verbose move-by-move
    if show_verbose:
        print(f"\n{BOLD}{C}  📋 MOVE-BY-MOVE ANALYSIS{RST}")
        print()
        for m in results["move_analysis"]:
            num = m["move_number"]
            san = m["move"]
            rank = m["move_rank"]
            diff = abs(m["score_diff"])

            if m["is_best"]:
                print(f"  {G}✓ {num}. {san:<8} #{rank}  ({diff:.0f}cp){RST}")
            else:
                best_san = m["best_move"] or "?"
                print(f"  {R}✗ {num}. {san:<8} #{rank}  (-{diff:.0f}cp)  best: {best_san}{RST}")
                if m.get("top_moves"):
                    for t in m["top_moves"][:3]:
                        marker = f"{G}→{RST}" if t["rank"] == 1 else f" {DIM} {RST}"
                        print(f"    {marker} {t['rank']}. {t['move']} ({t['score']}cp)")
        print()
        print(line)

    # Lichess share link
    if results.get("sacrifice_position_fen"):
        fen = results["sacrifice_position_fen"]
        color = results["player_color"]
        opponent = results.get("black", "?") if color == "white" else results.get("white", "?")
        fen_url = fen.replace(" ", "_")
        share_url = f"https://lichess.org/editor/{fen_url}?color={color}"
        print(f"{BOLD}{C}  🔗 CHALLENGE A FRIEND{RST}")
        print(f"{W}  Play from this position as {color} (original opponent: {opponent}):{RST}")
        print(f"  {C}{share_url}{RST}")
        print(line)

    print(f"{DIM}  Analysis time: {elapsed_time:.1f}s{RST}")
    print()


def main():
    """Command-line interface for the Dr Lupo Challenge analyzer."""
    parser = argparse.ArgumentParser(
        description="🎮 Dr Lupo Challenge Analyzer v2 👑",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python -m src.dr_lupo_analyzer https://lichess.org/XXXXXXXX --verbose"
    )
    parser.add_argument("url", help="URL to a Lichess game")
    parser.add_argument("--engine", help="Path to Stockfish engine")
    parser.add_argument("--depth", type=int, default=16, help="Engine analysis depth (default: 16)")
    parser.add_argument("--margin", type=float, default=25,
                      help="Margin of error in centipawns (default: 25)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed move-by-move analysis")
    parser.add_argument("--no-graph", action="store_true", help="Skip graph generation")
    parser.add_argument("--output", "-o", default="dr_lupo_analysis.png", help="Graph output path (default: dr_lupo_analysis.png)")

    args = parser.parse_args()

    print(f"\n⏳ Analyzing game: {args.url}")
    print(f"   Engine depth: {args.depth} | Margin: {args.margin}cp")
    print(f"   This may take a minute...\n")

    analyzer = DrLupoAnalyzer(
        engine_path=args.engine,
        engine_depth=args.depth,
        margin_cp=args.margin
    )

    start_time = time.time()
    results = analyzer.analyze_game(args.url)
    elapsed_time = time.time() - start_time

    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return 1

    if not results["queen_sacrificed"]:
        print("❌ No queen sacrifice found in the first 10 moves.")
        print("   The Dr Lupo Challenge requires sacrificing your queen early!")
        return 0

    # Add config to results for display
    results["engine_depth"] = args.depth
    results["margin_cp"] = args.margin

    # Print visual results
    print_visual_results(results, elapsed_time, show_verbose=args.verbose)

    # Generate graph
    if not args.no_graph:
        graph_path = generate_graph(results, output_path=args.output, margin_cp=args.margin)
        if graph_path:
            print(f"📈 Graph saved to: {graph_path}")
            # Try to open the graph
            import os
            os.startfile(graph_path) if sys.platform == "win32" else None

    return 0


if __name__ == "__main__":
    sys.exit(main())