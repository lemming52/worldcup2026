from __future__ import annotations
from pathlib import Path
import pandas as pd
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Place names in order of first mention in the Animaniacs "Yakko's World" song
# (lyrics.txt), 1-indexed. Stage directions and connector words ("and", "then",
# "Both", "*Faster music*", ...) are stripped out.
_SONG_ORDER: list[str] = [
    "United States", "Canada", "Mexico", "Panama",
    "Haiti", "Jamaica", "Peru",
    "Dominican Republic", "Cuba", "Caribbean",
    "Greenland", "El Salvador",
    "Puerto Rico", "Colombia", "Venezuela",
    "Honduras", "Guyana",
    "Guatemala", "Bolivia", "Argentina",
    "Ecuador", "Chile", "Brazil",
    "Costa Rica", "Belize", "Nicaragua", "Bermuda",
    "Bahamas", "Tobago", "San Juan",
    "Paraguay", "Uruguay", "Suriname",
    "French Guiana", "Barbados", "Guam",
    "Norway", "Sweden", "Iceland", "Finland",
    "Germany",
    "Switzerland", "Austria", "Czechoslovakia",
    "Italy", "Turkey", "Greece",
    "Poland", "Romania", "Scotland", "Albania",
    "Ireland", "Russia", "Oman",
    "Bulgaria", "Saudi Arabia", "Hungary",
    "Cyprus", "Iraq", "Iran",
    "Syria", "Lebanon", "Israel", "Jordan",
    "Yemen", "Kuwait", "Bahrain",
    "Netherlands", "Luxembourg", "Belgium", "Portugal",
    "France", "England", "Denmark", "Spain",
    "India", "Pakistan", "Burma", "Afghanistan",
    "Thailand", "Nepal", "Bhutan",
    "Kampuchea", "Malaysia", "Bangladesh", "Asia",
    "China", "Korea", "Japan",
    "Mongolia", "Laos", "Tibet", "Indonesia",
    "Philippine Islands", "Taiwan",
    "Sri Lanka", "New Guinea", "Sumatra", "New Zealand",
    "Borneo", "Vietnam",
    "Tunisia", "Morocco", "Uganda", "Angola",
    "Zimbabwe", "Djibouti", "Botswana",
    "Mozambique", "Zambia", "Swaziland", "Gambia",
    "Guinea", "Algeria", "Ghana",
    "Burundi", "Lesotho", "Malawi", "Togo",
    "Spanish Sahara",
    "Niger", "Nigeria", "Chad", "Liberia",
    "Egypt", "Benin", "Gabon",
    "Tanzania", "Somalia", "Kenya", "Mali",
    "Sierra Leone", "Algiers",
    "Dahomey", "Namibia", "Senegal", "Libya",
    "Cameroon", "Congo", "Zaire",
    "Ethiopia", "Guinea-Bissau", "Madagascar",
    "Rwanda", "Mahore", "Cayman",
    "Hong Kong", "Abu Dhabi", "Qatar", "Yugoslavia",
    "Crete", "Mauritania", "Transylvania",
    "Monaco", "Liechtenstein", "Malta", "Palestine",
    "Fiji", "Australia", "Sudan",
    "Montenegro", "Bosnia Herzegovina",
    "Soviet Union",
    "South Africa", "Georgia", "Moldovia", "Latvia",
    "Belarus", "Azerbaijan",
    "Uzbekistan", "Kazakhstan",
    "Tajikistan",
    "Turkmenistan", "Kyrgyzstan",
    "Armenia", "Tonga", "Palau",
    "Lithuania", "Serbia", "Kosovo",
    "US Samoa", "Balkans", "Brunei",
    "Macau", "Crimea", "Eritrea",
    "Ukraine", "Estonia", "Macedonia",
    "New Caledonia", "Eastern Slavonia",
    "Ivory Coast", "Cape Verde", "Andorra",
    "Solomon Islands", "Dubai",
]

# WC2026 team names that don't match a _SONG_ORDER entry directly: either the
# song uses an old/alternate name, or the team didn't exist in 1993 and shares
# a near neighbour's slot instead.
_TEAM_ALIASES: dict[str, str] = {
    "South Korea": "Korea",
    "Czechia": "Czechoslovakia",
    "Bosnia-Herzegovina": "Bosnia Herzegovina",
    "Türkiye": "Turkey",
    "Congo DR": "Zaire",          # Zaire = DR Congo's name at the time
    "Curaçao": "Netherlands",     # shares the Netherlands' slot
    "Croatia": "Yugoslavia",      # shares Yugoslavia's slot
}


class AnimaniacsRatingModel:
    """Effective Elo rating derived from a team's position in the Animaniacs
    "Yakko's World" song (lyrics.txt).

    Teams mentioned earlier in the song get a higher effective Elo; a team at
    the midpoint of the song gets the average FIFA Elo (mean fifa_points
    across all FIFA-ranked nations, from data/rankings.csv). The full range of
    real FIFA Elo points is spread linearly across the song's ~196 entries:

        elo_per_step = (max_fifa_points - min_fifa_points) / (len(_SONG_ORDER) - 1)
        mid_rank     = (1 + len(_SONG_ORDER)) / 2
        effective_elo(rank) = avg_fifa_points + elo_per_step * (mid_rank - rank)
    """

    name = "animaniacs"

    def __init__(self, rankings_path: Path | None = None) -> None:
        csv = rankings_path or (_DATA_DIR / "rankings.csv")
        df = pd.read_csv(csv)
        self._avg_elo = float(df["fifa_points"].mean())
        elo_range = float(df["fifa_points"].max() - df["fifa_points"].min())
        self._elo_per_step = elo_range / (len(_SONG_ORDER) - 1)
        self._mid_rank = (1 + len(_SONG_ORDER)) / 2

        self._rank: dict[str, int] = {
            place: i for i, place in enumerate(_SONG_ORDER, start=1)
        }

    def _song_rank(self, team_name: str) -> int:
        place = _TEAM_ALIASES.get(team_name, team_name)
        if place not in self._rank:
            raise KeyError(
                f"AnimaniacsRatingModel: '{team_name}' (-> '{place}') not found "
                "in the song order. Add an entry to _TEAM_ALIASES."
            )
        return self._rank[place]

    def rate(self, team: Team) -> float:
        rank = self._song_rank(team.name)
        return self._avg_elo + self._elo_per_step * (self._mid_rank - rank)
