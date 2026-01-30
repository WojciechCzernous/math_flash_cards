#!/usr/bin/env python3
"""
Parser for .tex flashcard files.

File format:
- Standard LaTeX document that compiles with pdflatex
- \section{Name} defines card categories/sections
- \begin{flashcard}{id} ... \end{flashcard} defines cards
- \Q{...} and \A{...} for question/answer
- %@rep:id:date:interval:ease for spaced repetition data (in comments)

Filename pattern: *_cards.tex
"""

import re
import os
import glob
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path


# Regex pattern for flashcard filenames
FLASHCARD_FILE_PATTERN = r".*_cards\.tex$"

# Compiled regex for file matching
FLASHCARD_FILE_RE = re.compile(FLASHCARD_FILE_PATTERN)


@dataclass
class RepetitionData:
    """Spaced repetition data for a card (SM-2 algorithm style)."""
    last_review: date | None = None
    interval: int = 1  # Days until next review
    ease_factor: float = 2.5  # Ease factor (min 1.3)
    repetitions: int = 0  # Number of successful reviews in a row
    
    def next_review_date(self) -> date | None:
        """Calculate the next review date."""
        if self.last_review is None:
            return None
        from datetime import timedelta
        return self.last_review + timedelta(days=self.interval)
    
    def is_due(self) -> bool:
        """Check if the card is due for review."""
        next_date = self.next_review_date()
        if next_date is None:
            return True  # Never reviewed
        return date.today() >= next_date
    
    def update(self, quality: int) -> None:
        """Update repetition data based on recall quality (0-5).
        
        Quality scale:
        0 - Complete blackout
        1 - Wrong, but recognized answer
        2 - Wrong, but answer seemed easy to recall
        3 - Correct with serious difficulty
        4 - Correct with some hesitation
        5 - Perfect response
        """
        self.last_review = date.today()
        
        if quality < 3:
            # Failed - reset
            self.repetitions = 0
            self.interval = 1
        else:
            # Success
            self.repetitions += 1
            if self.repetitions == 1:
                self.interval = 1
            elif self.repetitions == 2:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.ease_factor)
        
        # Update ease factor
        self.ease_factor = max(1.3, self.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    def to_string(self) -> str:
        """Serialize to string format for storage."""
        date_str = self.last_review.isoformat() if self.last_review else "none"
        return f"{date_str}:{self.interval}:{self.ease_factor:.2f}:{self.repetitions}"
    
    @classmethod
    def from_string(cls, s: str) -> "RepetitionData":
        """Parse from string format."""
        parts = s.split(":")
        if len(parts) >= 3:
            date_str = parts[0]
            last_review = None if date_str == "none" else date.fromisoformat(date_str)
            interval = int(parts[1])
            ease = float(parts[2])
            reps = int(parts[3]) if len(parts) > 3 else 0
            return cls(last_review=last_review, interval=interval, ease_factor=ease, repetitions=reps)
        return cls()


@dataclass 
class FlashCard:
    """A flashcard with question, answer, metadata, and repetition data."""
    id: str
    question: str
    answer: str
    section: str = "General"
    source_file: str = ""
    rep_data: RepetitionData = field(default_factory=RepetitionData)
    
    def is_due(self) -> bool:
        """Check if card is due for review."""
        return self.rep_data.is_due()


@dataclass
class FlashCardDeck:
    """A collection of flashcards from one or more files."""
    cards: list[FlashCard] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    
    def get_sections(self) -> list[str]:
        """Get all unique sections."""
        return sorted(set(card.section for card in self.cards))
    
    def filter_by_section(self, section: str) -> list[FlashCard]:
        """Get cards from a specific section."""
        return [c for c in self.cards if c.section == section]
    
    def get_due_cards(self) -> list[FlashCard]:
        """Get all cards due for review."""
        return [c for c in self.cards if c.is_due()]
    
    def get_card_by_id(self, card_id: str) -> FlashCard | None:
        """Find a card by its ID."""
        for card in self.cards:
            if card.id == card_id:
                return card
        return None


def find_flashcard_files(directory: str = ".") -> list[str]:
    """Find all flashcard .tex files in a directory.
    
    Pattern: *_cards.tex
    """
    pattern = os.path.join(directory, "*_cards.tex")
    files = glob.glob(pattern)
    return sorted(files)


def parse_flashcard_file(filepath: str) -> tuple[list[FlashCard], dict[str, RepetitionData]]:
    """Parse a .tex flashcard file.
    
    Returns:
        Tuple of (list of FlashCards, dict of card_id -> RepetitionData)
    """
    cards: list[FlashCard] = []
    rep_data: dict[str, RepetitionData] = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract repetition data from comments
    # Format: %@rep:card-id:date:interval:ease:reps
    rep_pattern = r'%@rep:([^:]+):(.+)'
    for match in re.finditer(rep_pattern, content):
        card_id = match.group(1)
        rep_str = match.group(2)
        rep_data[card_id] = RepetitionData.from_string(rep_str)
    
    # Track current section
    current_section = "General"
    
    # Find all sections
    section_pattern = r'\\section\{([^}]+)\}'
    sections = [(m.start(), m.group(1)) for m in re.finditer(section_pattern, content)]
    
    # Find all flashcards
    # Pattern: \begin{flashcard}{id} ... \Q{...} ... \A{...} ... \end{flashcard}
    card_pattern = r'\\begin\{flashcard\}\{([^}]+)\}(.*?)\\end\{flashcard\}'
    
    for match in re.finditer(card_pattern, content, re.DOTALL):
        card_id = match.group(1).strip()
        card_content = match.group(2)
        card_pos = match.start()
        
        # Determine section based on position
        for sec_pos, sec_name in reversed(sections):
            if sec_pos < card_pos:
                current_section = sec_name
                break
        
        # Extract question - handle both \Q{...} and \Qblock{...}
        q_match = re.search(r'\\Q(?:block)?\{((?:[^{}]|\{[^{}]*\})*)\}', card_content)
        question = q_match.group(1).strip() if q_match else ""
        
        # Extract answer - handle both \A{...} and \Ablock{...}
        a_match = re.search(r'\\A(?:block)?\{((?:[^{}]|\{[^{}]*\})*)\}', card_content)
        answer = a_match.group(1).strip() if a_match else ""
        
        if question and answer:
            card = FlashCard(
                id=card_id,
                question=question,
                answer=answer,
                section=current_section,
                source_file=filepath,
                rep_data=rep_data.get(card_id, RepetitionData())
            )
            cards.append(card)
    
    return cards, rep_data


def save_repetition_data(filepath: str, cards: list[FlashCard]) -> None:
    """Update repetition data in a .tex file.
    
    Adds or updates %@rep: comments after each flashcard.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Build a map of card_id -> new rep data string
    rep_updates: dict[str, str] = {}
    for card in cards:
        if card.source_file == filepath:
            rep_updates[card.id] = card.rep_data.to_string()
    
    # Remove existing rep data for cards we're updating
    for card_id in rep_updates:
        pattern = rf'%@rep:{re.escape(card_id)}:[^\n]*\n?'
        content = re.sub(pattern, '', content)
    
    # Add new rep data after each flashcard
    for card_id, rep_str in rep_updates.items():
        # Find the end of this flashcard
        pattern = rf'(\\end\{{flashcard\}})'
        # We need to find the right one - search for the flashcard with this id
        card_pattern = rf'(\\begin\{{flashcard\}}\{{{re.escape(card_id)}\}}.*?\\end\{{flashcard\}})'
        
        def add_rep_comment(match):
            return f"{match.group(1)}\n%@rep:{card_id}:{rep_str}"
        
        content = re.sub(card_pattern, add_rep_comment, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def load_deck_from_directory(directory: str = ".") -> FlashCardDeck:
    """Load all flashcard files from a directory into a deck."""
    deck = FlashCardDeck()
    
    files = find_flashcard_files(directory)
    for filepath in files:
        cards, _ = parse_flashcard_file(filepath)
        deck.cards.extend(cards)
        deck.source_files.append(filepath)
    
    return deck


def save_deck(deck: FlashCardDeck) -> None:
    """Save repetition data for all cards in the deck."""
    # Group cards by source file
    by_file: dict[str, list[FlashCard]] = {}
    for card in deck.cards:
        if card.source_file:
            by_file.setdefault(card.source_file, []).append(card)
    
    # Save each file
    for filepath, cards in by_file.items():
        save_repetition_data(filepath, cards)


# For testing
if __name__ == "__main__":
    print("Flashcard Parser Test")
    print("=" * 50)
    
    # Find files
    files = find_flashcard_files(".")
    print(f"\nFound {len(files)} flashcard file(s):")
    for f in files:
        print(f"  - {f}")
    
    # Load deck
    deck = load_deck_from_directory(".")
    print(f"\nLoaded {len(deck.cards)} card(s)")
    
    # Show sections
    sections = deck.get_sections()
    print(f"\nSections: {sections}")
    
    # Show cards
    for card in deck.cards[:5]:  # First 5
        print(f"\n[{card.id}] ({card.section})")
        print(f"  Q: {card.question[:50]}...")
        print(f"  A: {card.answer[:50]}...")
        print(f"  Due: {card.is_due()}")
