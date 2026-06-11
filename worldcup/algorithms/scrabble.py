from __future__ import annotations
import unicodedata
from worldcup.models import Team

# Standard English Scrabble tile values.
_LETTER_VALUES: dict[str, int] = {
    "A": 1, "B": 3, "C": 3, "D": 2, "E": 1, "F": 4, "G": 2, "H": 4, "I": 1,
    "J": 8, "K": 5, "L": 1, "M": 3, "N": 1, "O": 1, "P": 3, "Q": 10, "R": 1,
    "S": 1, "T": 1, "U": 1, "V": 4, "W": 4, "X": 8, "Y": 4, "Z": 10,
}


def letters(name: str) -> list[str]:
    """Strip accents/spaces/punctuation and return the A-Z letters of a name."""
    decomposed = unicodedata.normalize("NFKD", name)
    return [c.upper() for c in decomposed if c.isascii() and c.isalpha()]


def word_score(name: str) -> int:
    """Sum of standard Scrabble tile values for the letters in `name`."""
    return sum(_LETTER_VALUES[letter] for letter in letters(name))


class ScrabbleRatingModel:
    """Team strength derived from the Scrabble score of the country's name,
    played on a double word score square.

    Each letter of the team name scores its standard English Scrabble tile
    value (accents are stripped, e.g. Côte d'Ivoire -> COTEDIVOIRE; spaces,
    hyphens and apostrophes are ignored). The total is then doubled, as if
    the whole word landed on a double word score square:

        rating = 2 * sum(tile_value(letter) for letter in name)
    """

    name = "scrabble"

    def rate(self, team: Team) -> float:
        return float(2 * word_score(team.name))
