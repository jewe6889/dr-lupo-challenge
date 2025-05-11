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

    def __init__(self, engine_path=None, engine_depth=16, margin_cp=5):
        """
        Initialize the analyzer.
        
        Args:
            engine_path: Path to Stockfish engine. If None, will try to find it.
            engine_depth: Engine analysis depth.
            margin_cp: Margin of error in centipawns (default: 5).
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
            tuple: (queen_sacrificed, player_color, move_number, position_fen)
            or (False, None, None, None) if no sacrifice was found.
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
                
                # White's queen captured
                if captured_piece.color == chess.WHITE and white_queen_present:
                    white_has_queen = False
                    # Make the move to get to the position after sacrifice
                    board.push(move)
                    # Black sacrificed White's queen
                    return True, chess.BLACK, current_move, board.fen()
                
                # Black's queen captured
                elif captured_piece.color == chess.BLACK and black_queen_present:
                    black_has_queen = False
                    # Make the move to get to the position after sacrifice
                    board.push(move)
                    # White sacrificed Black's queen
                    return True, chess.WHITE, current_move, board.fen()
            
            # Make the move on our board
            board.push(move)
            
            # Update move counter (increment after White's move)
            if board.turn == chess.WHITE:
                current_move += 1
            
            # Stop if we've gone past the max move limit
            if current_move > max_move:
                break
        
        return False, None, None, None
    
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
                
                # Check if we've reached the starting move for analysis
                if current_move >= start_move and not sacrifice_reached:
                    sacrifice_reached = True
                    continue
                
                # Only analyze moves BY the player who sacrificed the queen, not against them
                if sacrifice_reached and board.turn == player_color:
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
            sacrifice_found, player_color, move_number, position_fen = (
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
                "player_color": "white" if player_color == chess.WHITE else "black",
                **analysis
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """Command-line interface for the Dr Lupo Challenge analyzer."""
    parser = argparse.ArgumentParser(description="Dr Lupo Challenge Analyzer")
    parser.add_argument("url", help="URL to a Lichess game")
    parser.add_argument("--engine", help="Path to Stockfish engine")
    parser.add_argument("--depth", type=int, default=16, help="Engine analysis depth (default: 16)")
    parser.add_argument("--margin", type=float, default=5, 
                      help="Margin of error in centipawns (default: 5)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed move analysis")
    
    args = parser.parse_args()
    
    print(f"Analyzing game: {args.url}")
    print(f"Engine depth: {args.depth}")
    print(f"Margin of error: {args.margin} centipawns")
    print("This may take several minutes. Please wait...")
    
    analyzer = DrLupoAnalyzer(
        engine_path=args.engine,
        engine_depth=args.depth,
        margin_cp=args.margin
    )
    
    start_time = time.time()
    results = analyzer.analyze_game(args.url)
    elapsed_time = time.time() - start_time
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return 1
    
    print("\nAnalysis Results:")
    print(f"Game: {results['white']} vs {results['black']}")
    
    if not results["queen_sacrificed"]:
        print("No queen sacrifice found in the first 10 moves.")
        return 0
    
    print(f"Queen sacrificed: Yes (Move {results['sacrifice_move']})")
    print(f"Position FEN: {results['sacrifice_position_fen']}")
    print(f"Player: {results['player']} ({results['player_color']})")
    print(f"Challenge completed: {'Yes' if results['challenge_completed'] else 'No'}")
    print(f"Accuracy: {results['accuracy']:.2f}%")
    print(f"Best moves: {results['best_moves']}/{results['total_moves_analyzed']}")
    print(f"Max consecutive best moves: {results['max_consecutive_best']}")
    print(f"Analysis time: {elapsed_time:.2f} seconds")
    
    # Print detailed move analysis if requested
    if args.verbose:
        # Check if terminal supports colors
        try:
            from colorama import init, Fore, Style
            init()
            has_colors = True
        except ImportError:
            has_colors = False
        
        print("\nDetailed Move Analysis:")
        
        for move in results["move_analysis"]:
            move_str = f"{move['move_number']}. {move['move']}"
            rank_info = f"(Rank: {move['move_rank']}, "
            
            if move['score_diff'] > 0:
                eval_info = f"Eval diff: -{abs(move['score_diff']):.2f}cp)"
            else:
                eval_info = f"Eval diff: +{abs(move['score_diff']):.2f}cp)"
            
            if has_colors:
                if move["is_best"]:
                    status = f"{Fore.GREEN}BEST{Style.RESET_ALL}"
                    move_info = f"{Fore.GREEN}{move_str} {status} {rank_info}{eval_info}{Style.RESET_ALL}"
                else:
                    status = f"{Fore.RED}NOT BEST{Style.RESET_ALL}"
                    move_info = f"{Fore.RED}{move_str} {status} {rank_info}{eval_info}{Style.RESET_ALL}"
                    best_move_info = f"\n  {Fore.GREEN}Best: {move['best_move']}{Style.RESET_ALL}"
                    move_info += best_move_info
            else:
                status = "✓" if move["is_best"] else "✗"
                move_info = f"{move_str} {status} {rank_info}{eval_info}"
                if not move["is_best"]:
                    move_info += f"\n  Best: {move['best_move']}"
            
            print(move_info)
            
            # Show top moves
            if not move["is_best"] and args.verbose:
                print("  Top moves:")
                for top_move in move["top_moves"][:3]:  # Show top 3 moves
                    if has_colors:
                        rank_color = Fore.GREEN if top_move["rank"] == 1 else Fore.YELLOW
                        print(f"  {rank_color}{top_move['rank']}. {top_move['move']} ({top_move['score']}cp){Style.RESET_ALL}")
                    else:
                        print(f"  {top_move['rank']}. {top_move['move']} ({top_move['score']}cp)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())