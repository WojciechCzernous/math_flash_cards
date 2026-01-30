#!/usr/bin/env python3
"""
Math Flash Cards - A console-based flashcard app with LaTeX rendering.
Uses matplotlib for LaTeX rendering and imgcat for terminal display.

Loads flashcards from .tex files (*_cards.tex) in the current directory.
"""

import io
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from imgcat import imgcat

from card_parser import (
    FlashCard, FlashCardDeck, RepetitionData,
    load_deck_from_directory, save_deck, find_flashcard_files
)

# Enable full LaTeX rendering - requires LaTeX installation (e.g., MacTeX)
# If you don't have LaTeX installed, set this to False
USE_LATEX = True

if USE_LATEX:
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
    })


def render_latex(text: str, fontsize: int = 24) -> None:
    """Render text with LaTeX math and display in terminal using imgcat.
    
    With USE_LATEX=True, write naturally:
        "Solve: $x^2 - 5x + 6 = 0$"
    
    With USE_LATEX=False, everything must be in math mode:
        r"$\\text{Solve: } x^2 - 5x + 6 = 0$"
    """
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.axis('off')
    ax.text(
        0.5, 0.5,
        text,
        fontsize=fontsize,
        ha='center',
        va='center',
        transform=ax.transAxes
    )
    
    # Save to buffer and display with imgcat
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', 
                facecolor='white', edgecolor='none', dpi=150)
    buf.seek(0)
    plt.close(fig)
    
    imgcat(buf.read())


class FlashCardApp:
    """Main application for running the flashcard quiz."""
    
    def __init__(self, deck: FlashCardDeck | None = None, directory: str = "."):
        if deck:
            self.deck = deck
        else:
            self.deck = load_deck_from_directory(directory)
        
        self.cards: list[FlashCard] = list(self.deck.cards)
        self.current_index = 0
        self.score = 0
        self.total_attempted = 0
        self.reviewed_cards: list[FlashCard] = []  # Track for saving
    
    def shuffle(self) -> None:
        """Shuffle the flashcards."""
        random.shuffle(self.cards)
        self.current_index = 0
    
    def get_sections(self) -> list[str]:
        """Get all unique sections."""
        return self.deck.get_sections()
    
    def filter_by_section(self, section: str) -> None:
        """Filter cards to only show a specific section."""
        self.cards = [c for c in self.cards if c.section == section]
        self.current_index = 0
    
    def filter_due_only(self) -> None:
        """Filter to only show cards due for review."""
        self.cards = [c for c in self.cards if c.is_due()]
        self.current_index = 0
    
    def show_question(self, card: FlashCard) -> None:
        """Display the question using LaTeX rendering."""
        print("\n" + "=" * 50)
        print("📝 QUESTION:")
        print("=" * 50)
        render_latex(card.question)
    
    def show_answer(self, card: FlashCard) -> None:
        """Display the answer using LaTeX rendering."""
        print("\n" + "-" * 50)
        print("✅ ANSWER:")
        print("-" * 50)
        render_latex(card.answer)
    
    def run_quiz(self) -> None:
        """Run an interactive quiz session."""
        print("\n" + "🎓 " + "=" * 46 + " 🎓")
        print("       MATH FLASH CARDS")
        print("🎓 " + "=" * 46 + " 🎓")
        print(f"\nTotal cards: {len(self.cards)}")
        print("\nCommands:")
        print("  [Enter] - Show answer")
        print("  [1-5]   - Rate recall (1=forgot, 5=perfect)")
        print("  [s]     - Skip card")
        print("  [q]     - Quit")
        
        self.shuffle()
        
        while self.current_index < len(self.cards):
            card = self.cards[self.current_index]
            
            due_info = "📅 DUE" if card.is_due() else "⏳ scheduled"
            print(f"\n📌 Card {self.current_index + 1}/{len(self.cards)} "
                  f"[{card.section}] [{card.id}] {due_info}")
            
            self.show_question(card)
            
            user_input = input("\nPress Enter to reveal answer (or 's' to skip, 'q' to quit): ").strip().lower()
            
            if user_input == 'q':
                break
            elif user_input == 's':
                self.current_index += 1
                continue
            
            self.show_answer(card)
            
            while True:
                result = input("\nRate your recall (1=forgot, 2=hard, 3=ok, 4=good, 5=perfect): ").strip()
                if result in ['1', '2', '3', '4', '5']:
                    quality = int(result)
                    # Convert 1-5 to 0-5 scale for SM-2
                    sm2_quality = quality  # 1->1, 2->2, 3->3, 4->4, 5->5
                    if quality <= 2:
                        sm2_quality = quality - 1  # 1->0, 2->1 (failures)
                    else:
                        sm2_quality = quality  # 3,4,5 stay same (successes)
                    
                    card.rep_data.update(sm2_quality)
                    self.reviewed_cards.append(card)
                    self.total_attempted += 1
                    
                    if quality >= 3:
                        self.score += 1
                        next_review = card.rep_data.next_review_date()
                        print(f"🎉 Next review: {next_review}")
                    else:
                        print("📚 Card will be reviewed again soon!")
                    break
                elif result == 'q':
                    self.current_index = len(self.cards)
                    break
                else:
                    print("Please enter 1-5")
            
            self.current_index += 1
        
        # Save progress
        if self.reviewed_cards:
            save_deck(self.deck)
            print("\n💾 Progress saved!")
        
        self.show_results()
    
    def show_results(self) -> None:
        """Display quiz results."""
        print("\n" + "=" * 50)
        print("📊 QUIZ RESULTS")
        print("=" * 50)
        if self.total_attempted > 0:
            percentage = (self.score / self.total_attempted) * 100
            print(f"Score: {self.score}/{self.total_attempted} ({percentage:.1f}%)")
            
            if percentage >= 90:
                print("🏆 Excellent! You're a math master!")
            elif percentage >= 70:
                print("👍 Good job! Keep it up!")
            elif percentage >= 50:
                print("💪 Not bad! Practice makes perfect!")
            else:
                print("📖 Keep studying! You'll get there!")
        else:
            print("No cards attempted.")
        print("=" * 50 + "\n")


def main():
    """Main entry point."""
    print("\n" + "=" * 50)
    print("  Welcome to Math Flash Cards! 🧮")
    print("=" * 50)
    
    # Find flashcard files
    files = find_flashcard_files(".")
    
    if not files:
        print("\n⚠️  No flashcard files found!")
        print("   Looking for: *_cards.tex")
        print("\n   Create a file like 'algebra_cards.tex' with this structure:")
        print("""
   \\begin{flashcard}{my-card-01}
   \\Q{Your question with $math$}
   \\A{Your answer}
   \\end{flashcard}
        """)
        print("   See example_cards.tex for a complete template.")
        return
    
    print(f"\n📁 Found {len(files)} flashcard file(s):")
    for f in files:
        print(f"   • {Path(f).name}")
    
    # Load deck
    app = FlashCardApp(directory=".")
    
    if not app.cards:
        print("\n⚠️  No cards parsed from files. Check file format.")
        return
    
    print(f"\n📚 Loaded {len(app.cards)} cards")
    
    # Show due cards info
    due_cards = app.deck.get_due_cards()
    print(f"📅 Due for review: {len(due_cards)} cards")
    
    # Section selection
    sections = app.get_sections()
    print("\n📂 Sections:")
    for i, sec in enumerate(sections, 1):
        count = len([c for c in app.cards if c.section == sec])
        due_count = len([c for c in app.cards if c.section == sec and c.is_due()])
        print(f"   {i}. {sec} ({count} cards, {due_count} due)")
    print(f"   {len(sections) + 1}. All sections")
    print(f"   {len(sections) + 2}. Due cards only")
    
    try:
        choice = input("\nSelect option (number) or press Enter for all: ").strip()
        if choice and choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(sections):
                app.filter_by_section(sections[idx - 1])
                print(f"\n✓ Selected: {sections[idx - 1]}")
            elif idx == len(sections) + 2:
                app.filter_due_only()
                print(f"\n✓ Showing {len(app.cards)} due cards only")
    except (ValueError, IndexError):
        pass
    
    if not app.cards:
        print("\n✨ No cards to review! All caught up!")
        return
    
    app.run_quiz()


if __name__ == "__main__":
    main()
