# Vision: Chess Quality Above All

## The Problem

Modern chess culture increasingly rewards speed over beauty. Blitz, bullet, and rapid formats dominate online play. Most games aren't decided by brilliant ideas — they're decided by whoever blunders last under time pressure. The art of deep, precise, *beautiful* chess is being drowned out by the clock.

Engine moves are often strikingly elegant. The best move in a position can be shocking, counterintuitive, and deeply satisfying — but we rarely get to see that from human players because the format doesn't reward it.

**What if we built a platform that celebrated quality above everything else?**

---

## The Core Philosophy

> One bad move and it's over.

No time pressure. No rating anxiety. Just you, the position, and the relentless demand for perfection. Every challenge should feel like walking a tightrope — exhilarating when you succeed, devastating when you slip.

---

## The Dr Lupo Challenge — And What It Could Become

### Current: The Original Dr Lupo Challenge
- Sacrifice your queen within the first 10 moves
- Play 26 consecutive best engine moves from the resulting position
- Binary: you either did it or you didn't

This is already brutal. But it's just the beginning.

---

## Challenge Modes

### 1. The Lupo Ladder 🪜
The classic Dr Lupo formula — sacrifice your queen in the first 10 moves, then play perfect engine moves from the resulting chaos — but at every difficulty level.

| Tier | Required Streak | Badge |
|------|----------------|-------|
| **Baby Lupo** | 3 consecutive best moves | 🍼 |
| **Padawan Lupo** | 5 consecutive best moves | 🔵 |
| **Prodigy Lupo** | 7 consecutive best moves | 🟢 |
| **Half Lupo** | 13 consecutive best moves | 🟡 |
| **Master Lupo** | 20 consecutive best moves | 🟠 |
| **Dr Lupo** | 26 consecutive best moves | 👑 |

- Positions come from random queen sacrifices — every attempt is a fresh position
- You climb the ladder: each tier unlocks after completing the one below
- Your best streak is always tracked, even if it falls between tiers
- Sharing shows your tier + the position, so friends can try the same one

### 2. Immortal Lupo 🏛️
Same concept — play N consecutive best engine moves — but from **famous positions in chess history**. No queen sacrifice required; the position *is* the challenge.

- A curated library of critical moments from legendary games
- Positions where brilliance actually happened: Kasparov's immortal, Fischer's game of the century, Tal's sacrifices, Morphy's opera game...
- Same tier system (Baby → Dr Lupo) applies to the required streak length
- The twist: you're playing from where a grandmaster stood — can you match them?
- Each position comes with historical context: who played it, when, what was at stake
- Completing a position "unlocks" the grandmaster's actual continuation for comparison

### 3. Superintelligent Lupo 🤖
Same streak concept, but positions are extracted from **engine-vs-engine games** — the most complex, inhuman, razor-sharp positions that exist in chess.

- Positions from Stockfish vs Leela Chess Zero games, TCEC seasons, etc.
- These positions have no human intuition to lean on — pure calculation
- Same tier system applies
- The difficulty is naturally higher: engine games produce positions where even strong players struggle to find the best move
- A humbling mode — this is what perfect chess looks like, and it's alien
- Leaderboard tracks the highest tier anyone has achieved from engine positions

### 4. Survival Lupo ☠️
One mistake and you're dead — but every best move you find branches the game forward.

**How it works:**
- Start from a position in a real titled-player game
- You must find **one of the best moves** (within 49cp) to survive
- If a position has multiple best moves, finding ANY one counts — you live
- **The twist:** each time you survive, the game **continues from your move**, not the game's move — you're writing your own line
- After your move, the opponent replies (from the actual game or engine-chosen response), and you face the next position
- One miss = game over. Your score is how many consecutive positions you survived
- If you find the best move AND there are other best moves, you get a **bonus indicator** but the game still branches from your chosen move

**Why this is different from the Live Scoring challenge:**
- Live Scoring plays through the actual game line regardless of what you play — you're graded on each position independently
- Survival branches: your move determines the NEXT position you face — the game tree diverges from the original
- This means two players who make different (but both "best") choices on move 5 will face completely different positions from move 6 onward
- The skill ceiling is higher: not only must you find best moves, you must find best moves in positions that arise from YOUR previous best moves, which may be unfamiliar territory

**Scoring & tiers:**
- Score = number of consecutive positions survived
- Same tier badges apply (Baby 3, Padawan 5, Prodigy 7, Half Lupo 13, Master 20, Dr Lupo 26)
- Sharing shows the branching tree visually — where you diverged from the original game

### 5. Dr Lupo Challenge of the Day 📅
Every day, one position. Everyone plays it. A global leaderboard reveals who played the most beautifully.

**How it works:**
- At midnight UTC, a new position drops (rotates between Ladder, Immortal, and Superintelligent sources)
- Every player gets the same position and plays from it
- Your score: number of consecutive best engine moves from that position (max 26)
- No retries — one shot per day

**The live histogram:**
- A graph updated in real-time shows the distribution of all players' scores
- X-axis: number of consecutive best moves (0–26), Y-axis: number of players
- The shape of the histogram *tells a story*: a big spike at move 8 means there's a brutally hard move at move 9 — players can see where others are failing without spoilers
- After you've submitted your attempt, the histogram becomes fully visible with annotations showing the critical "wall" moves where most players cracked

**Leaderboard & streaks:**
- Daily leaderboard with rankings
- Weekly/monthly aggregate: consistency matters — who can stay sharp day after day?
- "Daily streak" counter: how many consecutive days you've scored 10+? 15+? 20+?
- End-of-week summary shared as a Wordle-style grid: one row per day, showing how far you got

---

## Scoring & Identity

### The Beauty Score (BS)
Instead of Elo (which rewards winning, regardless of how), a **Beauty Score** — a persistent rating based purely on the precision of your play across all challenge modes.

- Calculated from your best streaks across all modes, weighted by difficulty:
  - Lupo Ladder positions: 1x multiplier
  - Immortal Lupo positions: 1.5x (historical positions tend to be harder to read)
  - Superintelligent Lupo positions: 2x (inhuman positions, maximum difficulty)
- Daily Challenge consistency adds a bonus: sustained excellence > one-off brilliance
- Decays slowly over time — you must keep proving yourself
- Publicly visible on your profile: "This player doesn't just win, they play *beautifully*"

### Achievement System

**Lupo Ladder**
- 🍼 **Baby Steps**: Complete Baby Lupo (3 consecutive best moves)
- � **Padawan**: Complete Padawan Lupo (5)
- 🟢 **Prodigy**: Complete Prodigy Lupo (7)
- 🟡 **Halfway There**: Complete Half Lupo (13)
- 🟠 **Master Class**: Complete Master Lupo (20)
- 👑 **Dr Lupo**: Complete the full 26-move challenge

**Immortal Lupo**
- 🏛️ **History Student**: Complete any Immortal Lupo at Baby tier
- ⚔️ **Walking With Giants**: Complete any Immortal Lupo at Dr Lupo tier
- 🏆 **The Immortal**: Complete 10 different Immortal Lupo positions at Dr Lupo tier

**Superintelligent Lupo**
- 🤖 **Silicon Dreams**: Complete any Superintelligent Lupo at Baby tier
- 🧠 **Beyond Human**: Complete any Superintelligent Lupo at Master tier
- 💎 **Singularity**: Complete any Superintelligent Lupo at Dr Lupo tier

**Daily Challenge**
- 📅 **Regular**: Complete 7 daily challenges in a row
- 🔥 **On Fire**: Score 13+ on 5 consecutive daily challenges
- 🌟 **Daily Champion**: Finish #1 on the daily leaderboard
- 📊 **The Wall**: Be the move where 50%+ of players fail on a daily challenge (your position held)

---

## Social & Sharing

- Wordle-style shareable grids (already implemented for Dr Lupo)
- Challenge friends to the same position — "I got 23/26 from this position, can you beat me?"
- Daily Challenge histogram is the centerpiece social feature: watching the spike form in real-time as players hit the same wall is addictive
- Weekly summary card: your 7 daily scores as a color-coded row (share on socials)
- Replays of perfect runs: watch someone nail 26 moves in a row — it should feel like watching a highlight reel
- Compare your daily histogram position against friends: "You cracked at move 14? I held until 19 😏"

---

## What This Is NOT

- This is not a rating system replacement
- This is not about making chess "easier" or "more accessible"
- This is about carving out a space where **quality is the only thing that matters**
- A place where the 1400 who plays 20 perfect moves gets more respect than the 2200 who wins on time

---

## Technical Direction

- All challenges share the same core engine analysis pipeline (already built for Dr Lupo v2)
- Position generation can use curated databases + random generation with engine validation
- Web UI with Lichess board embedding for interactive play
- API-first design so challenges can be played via CLI, web, or browser extension
- Configurable difficulty: engine depth, margin of error (centipawns), number of required moves

### Lichess Chrome Extension
The most natural home for this is a **Lichess Chrome extension** that integrates directly into the game experience:

- **Post-game overlay**: after finishing a game on Lichess, the extension detects if a queen sacrifice happened and automatically offers to run the Dr Lupo analysis
- **Badge display on profile**: show your highest Lupo tier badge next to your username
- **Daily Challenge tab**: a dedicated panel in the Lichess sidebar for the daily challenge, with the live histogram updating as players submit
- **One-click analysis**: right-click any game in your history → "Run Dr Lupo Challenge"
- **Inline graph**: the move rank + eval diff graph renders directly in the Lichess analysis board, no separate window needed
- **Social integration**: share results directly to Lichess chat, Discord, or as a screenshot
- Uses the Lichess API for game data and a lightweight backend for engine analysis + leaderboard persistence

---

*The clock is the enemy of beauty. Let's build something that reminds people what chess is supposed to look like.*
