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

```bash
python -m src.dr_lupo_analyzer https://lichess.org/Fqxk7kf8gtAo
```

Optional parameters:
- `--engine`: Path to the Stockfish engine (auto-detected by default)
- `--depth`: Engine analysis depth (default: 16)
- `--margin`: Margin of error in centipawns (default: 0.05)

### Web Interface

Run the Flask application:

```bash
python app.py
```

Then open your browser and navigate to http://localhost:5000

## Example Analysis

Analyzing a game with a queen sacrifice:

```
Analyzing game: https://lichess.org/Fqxk7kf8gtAo
Engine depth: 16
Margin of error: 0.05 centipawns
This may take several minutes. Please wait...

Analysis Results:
Game: DrLupo vs RandomOpponent
Queen sacrificed: Yes (Move 8)
Position FEN: rnb1kb1r/pppp1ppp/5n2/4p3/2B1P3/2N5/PPP2PPP/R1BqK2R w KQkq - 0 7
Player: DrLupo (white)
Challenge completed: No
Accuracy: 75.00%
Best moves: 18/24
Max consecutive best moves: 10
```

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

## License

MIT
