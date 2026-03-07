# Dr Lupo Challenge Analyzer v2

A tool to analyze chess games and determine if a player has completed the "Dr Lupo Challenge."

## The Challenge

The Dr Lupo Challenge requires a player to:
1. Sacrifice their queen within the first 10 moves of the game
2. Follow up with 26 consecutive "best" engine moves (within a configurable centipawn tolerance)

### The Lupo Ladder

| Tier | Required Streak | Badge |
|------|----------------|-------|
| Baby Lupo | 3 consecutive | 🍼 |
| Padawan Lupo | 5 consecutive | 🔵 |
| Prodigy Lupo | 7 consecutive | 🟢 |
| Half Lupo | 13 consecutive | 🟡 |
| Master Lupo | 20 consecutive | 🟠 |
| Dr Lupo | 26 consecutive | 👑 |

## Features

- Detects queen sacrifices within the first 10 moves
- Analyzes post-sacrifice moves using Stockfish engine
- Badge system based on consecutive best-move streaks
- Visual analysis graph (move ranks + eval diffs with tolerance zone)
- Wordle-style move grid and Lichess share link for friends to try the same position
- Color-coded CLI output with detailed move-by-move analysis
- Configurable engine depth, tolerance (centipawns), and move count

## Prerequisites

- Python 3.7+
- [Stockfish](https://stockfishchess.org/download/) chess engine

## Installation

```bash
git clone https://github.com/yourusername/dr-lupo-challenge.git
cd dr-lupo-challenge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Basic analysis
python -m src.dr_lupo_analyzer https://lichess.org/XXXXXXXX

# With Stockfish path and verbose output
python -m src.dr_lupo_analyzer https://lichess.org/XXXXXXXX --engine /path/to/stockfish --verbose

# Custom settings
python -m src.dr_lupo_analyzer https://lichess.org/XXXXXXXX --depth 20 --margin 10
```

Options:
- `--engine`: Path to Stockfish (auto-detected by default)
- `--depth`: Engine analysis depth (default: 16)
- `--margin`: Tolerance in centipawns (default: 25)
- `--verbose` / `-v`: Show move-by-move analysis with top engine choices
- `--no-graph`: Skip graph generation
- `--output` / `-o`: Graph output path (default: `dr_lupo_analysis.png`)

### Web Interface

```bash
python app.py
```

Then open http://localhost:5000

## Example Output

```
🎮  DR LUPO CHALLENGE v2  👑
──────────────────────────────────────────────────────────────
  Game:    jewe6889 vs lichess AI level 5
  Player:  jewe6889 (white)
──────────────────────────────────────────────────────────────
  👑 QUEEN SACRIFICE
  Move 9 · White gave up the queen (gxf6)
──────────────────────────────────────────────────────────────
  📊 CHALLENGE RESULTS
  Accuracy:     50.0% (13/26 best moves)
  Best streak:  3 consecutive best moves
  Tolerance:    25cp
  Completed:    ❌ NO

  🏆 BADGE: 🍼  Baby Lupo  (streak ≥ 3)

  Move grid:
  🟨🟥🟩🟩🟥🟥🟩🟩🟥
  🟥🟥🟥🟩🟩🟥🟥🟩🟥
  🟥🟥🟩🟩🟩🟥🟩🟩🟩
──────────────────────────────────────────────────────────────
  🔗 CHALLENGE A FRIEND
  Play from this position as white:
  https://lichess.org/editor/...?color=white
──────────────────────────────────────────────────────────────
```

The `--verbose` flag adds per-move details: rank, eval diff, and top engine alternatives.

A graph (`dr_lupo_analysis.png`) is generated automatically showing move ranks as colored bars and eval diffs as a line, with the tolerance zone highlighted in green.

## Troubleshooting

- **Stockfish not found**: specify the path with `--engine /path/to/stockfish`
- **Too slow**: reduce depth with `--depth 8`
- **No colors**: install colorama with `pip install colorama`

## License

MIT
