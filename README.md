# Dr Lupo Challenge Analyzer

A tool to analyze chess games and determine if a player has completed the "Dr Lupo Challenge."

## The Challenge

The Dr Lupo Challenge requires a player to:
1. Sacrifice their queen within the first 10 moves of the game
2. Follow up with 26 consecutive "best" engine moves

## Features

- Detects queen sacrifices within the first 10 moves of a chess game
- Analyzes game moves after the sacrifice using Stockfish engine
- Calculates accuracy score (proportion of best engine moves)
- Tracks maximum consecutive best moves played
- Returns the FEN position after the queen sacrifice for further analysis
- Provides detailed move analysis with rank and evaluation differences
- Shows alternative best moves and top engine choices
- Color-coded output in CLI and web interface
- Configurable engine depth and margin of error for move assessment

## Prerequisites

- Python 3.7+
- Stockfish chess engine installed on your system

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/dr-lupo-challenge.git
cd dr-lupo-challenge
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Stockfish

The analyzer requires Stockfish to be installed on your system. You can download it from [the official website](https://stockfishchess.org/download/).

Make sure the stockfish executable is in your system PATH or provide the path using the `--engine` flag.

## Usage

### Command Line Interface

Basic usage:
```bash
python -m src.dr_lupo_analyzer https://lichess.org/Fqxk7kf8gtAo
```

For detailed move analysis:
```bash
python -m src.dr_lupo_analyzer https://lichess.org/Fqxk7kf8gtAo --verbose
```

Optional parameters:
- `--engine`: Path to the Stockfish engine (auto-detected by default)
- `--depth`: Engine analysis depth (default: 16)
- `--margin`: Margin of error in centipawns (default: 5)
- `--verbose`: Show detailed move analysis with rankings and top moves

### Web Interface

Run the Flask application:

```bash
python app.py
```

Then open your browser and navigate to http://localhost:5000

## Example

Analyzing a game with a queen sacrifice:

```
Analyzing game: https://lichess.org/Fqxk7kf8gtAo
Engine depth: 16
Margin of error: 5 centipawns
This may take several minutes. Please wait...

Analysis Results:
Game: lichess AI level 3 vs jewe
Queen sacrificed: Yes (Move 9)
Position FEN: r1b1kb1r/1pp2ppp/p1n2n2/4p3/4P3/2PQ1P2/P1PP2PP/R1B1KB1R b KQkq - 0 9
Player: lichess AI level 3 (white)
Challenge completed: No
Accuracy: 34.62%
Best moves: 9/26
Max consecutive best moves: 2
Analysis time: 25.89 seconds
```

With the `--verbose` flag, you'll see additional information for each move:
- Move rank (compared to best moves)
- Evaluation difference (how far the move is from the best move in centipawns)
- Top alternative moves
- Color-coded output (green for best moves, red for non-best moves)

## Troubleshooting

### Stockfish Not Found
If you get an error that Stockfish is not found, you can specify the path directly:
```bash
python -m src.dr_lupo_analyzer https://lichess.org/Fqxk7kf8gtAo --engine /path/to/stockfish
```

### Analysis Takes Too Long
You can reduce the engine depth for faster (but less accurate) analysis:
```bash
python -m src.dr_lupo_analyzer https://lichess.org/Fqxk7kf8gtAo --depth 8
```

### Colorama Not Found
If you want colored CLI output but get an error about colorama, install it:
```bash
pip install colorama
```

## License

MIT
