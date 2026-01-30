# Math Flash Cards 🧮

A console-based math flashcard application with beautiful LaTeX rendering using matplotlib and imgcat.

## Features

- 📝 **LaTeX Rendering** - Beautiful mathematical notation displayed directly in your terminal
- 📁 **File-based Cards** - Store Q&A in `.tex` files, editable in any LaTeX IDE
- 🗂️ **Sections** - Organize cards into sections within each file
- 🔄 **Spaced Repetition** - SM-2 algorithm tracks your progress
- 📅 **Due Cards** - Focus on cards that need review
- 💾 **Auto-save** - Progress saved automatically to your .tex files

## Requirements

- **iTerm2** (for imgcat support) or another terminal with inline image support
- Python 3.10+
- macOS (recommended)
- **LaTeX distribution** (for full LaTeX mode) - see below

## Installation

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### LaTeX Installation (Recommended)

For natural LaTeX syntax where you can mix text and math freely (e.g., `r"Solve: $x^2 = 4$"`), you need a LaTeX distribution:

```bash
# Full MacTeX (~4GB)
brew install --cask mactex-no-gui

# Or smaller BasicTeX (~100MB)
brew install --cask basictex
```

After installing, restart your terminal or run:
```bash
eval "$(/usr/libexec/path_helper)"
```

**Without LaTeX:** Set `USE_LATEX = False` in `flashcards.py`. You'll need to use the `\text{}` syntax inside math mode (e.g., `r"$\text{Solve: } x^2 = 4$"`).

## Usage

```bash
python flashcards.py
```

The app automatically finds all `*_cards.tex` files in the current directory.

### Controls

| Key | Action |
|-----|--------|
| `Enter` | Show answer |
| `1-5` | Rate recall (1=forgot, 5=perfect) |
| `s` | Skip card |
| `q` | Quit quiz |

## Creating Flashcard Files

### File Naming

Files must match the pattern: `*_cards.tex`

Examples:
- `algebra_cards.tex`
- `calculus_cards.tex`
- `exam_prep_cards.tex`

### File Structure

```tex
\documentclass[11pt]{article}
\input{flashcard_preamble}  % Optional: for nice PDF rendering

\begin{document}

\section{Quadratic Equations}

\begin{flashcard}{quad-001}
\Q{Solve: $x^2 - 5x + 6 = 0$}
\A{$x = 2$ or $x = 3$}
\end{flashcard}

\begin{flashcard}{quad-002}
\Q{What is the quadratic formula?}
\A{$x = \displaystyle\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$}
\end{flashcard}

\section{Another Section}

\begin{flashcard}{other-001}
\Q{Your question here}
\A{Your answer here}
\end{flashcard}

\end{document}
```

### Key Elements

| Element | Purpose |
|---------|---------|
| `\section{Name}` | Groups cards into selectable sections |
| `\begin{flashcard}{id}` | Card with unique ID for tracking |
| `\Q{...}` | Question (supports mixed text + $math$) |
| `\A{...}` | Answer |

### Card IDs

Each card needs a unique ID for spaced repetition tracking:
- Use descriptive prefixes: `calc-001`, `trig-005`, `def-theorem-01`
- IDs are stored with review data in comments

### Repetition Data

The app automatically saves your progress as LaTeX comments:
```tex
\begin{flashcard}{quad-001}
\Q{...}
\A{...}
\end{flashcard}
%@rep:quad-001:2026-01-30:6:2.50:2
```

Format: `%@rep:id:last-review:interval-days:ease-factor:repetitions`

### Tips

1. **Use `\displaystyle`** for full-size fractions and operators:
   ```tex
   \Q{$\displaystyle\int x^n \, dx = \;?$}
   ```

2. **Compile to PDF** to preview your cards in a LaTeX IDE

3. **Include the preamble** for nice formatting when viewing as PDF:
   ```tex
   \input{flashcard_preamble}
   ```

## Files Overview

| File | Purpose |
|------|---------|
| `flashcards.py` | Main app |
| `card_parser.py` | Parses .tex files |
| `flashcard_preamble.tex` | LaTeX macros for PDF rendering |
| `example_cards.tex` | Sample cards to get started |

## License

MITMIT
