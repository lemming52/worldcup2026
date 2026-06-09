"""Build data/rankings.csv by joining FIFA rankings with the Equaldex LGBT equality index.

FIFA data: fetched live from inside.fifa.com (falls back to April 1, 2026 hardcoded data).
Equality data: Equaldex equality index (scraped June 2026, 197 countries, 0-100).

Run from project root:
    python scripts/build_rankings.py
"""

from pathlib import Path
import pandas as pd

# ── Equaldex LGBT equality index (0 = least equal, 100 = most equal) ─────────
EQUALITY_INDEX: dict[str, int] = {
    "Iceland": 93, "Norway": 88, "Uruguay": 87, "Spain": 83, "Denmark": 82,
    "New Zealand": 81, "Malta": 80, "Chile": 80, "Germany": 80, "Andorra": 80,
    "Canada": 78, "Australia": 78, "Belgium": 78, "Portugal": 77, "Cuba": 77,
    "Finland": 76, "Netherlands": 76, "Sweden": 75, "Brazil": 75, "France": 74,
    "Argentina": 74, "Austria": 73, "Czechia": 72, "Colombia": 71, "Mexico": 71,
    "Switzerland": 70, "Ireland": 70, "Nepal": 69, "Costa Rica": 69,
    "Liechtenstein": 69, "United Kingdom": 68, "Cape Verde": 68,
    "United States": 68, "Luxembourg": 67, "South Africa": 67, "San Marino": 67,
    "Italy": 66, "Greece": 66, "Ecuador": 65, "Thailand": 65, "Slovenia": 65,
    "Bolivia": 62, "Israel": 62, "Seychelles": 61, "Taiwan": 59, "Estonia": 58,
    "Cyprus": 58, "Croatia": 57, "Botswana": 56, "China": 56, "Montenegro": 55,
    "Barbados": 55, "Fiji": 55, "Timor-Leste": 54, "Peru": 54, "Philippines": 54,
    "Japan": 53, "Monaco": 53, "Bhutan": 53, "Venezuela": 52, "Vietnam": 51,
    "Mauritius": 51, "Poland": 51, "Mozambique": 51, "India": 51,
    "Bosnia and Herzegovina": 50, "Serbia": 50, "Belize": 50, "Slovakia": 49,
    "North Macedonia": 49, "Marshall Islands": 49, "Hungary": 49, "Ukraine": 48,
    "Kosovo": 48, "Micronesia": 48, "Albania": 47, "Lithuania": 47, "Romania": 47,
    "Latvia": 46, "Sao Tome and Principe": 46, "South Korea": 46, "Honduras": 46,
    "Cambodia": 46, "Nicaragua": 45, "Laos": 45, "Lesotho": 44, "Singapore": 44,
    "Nauru": 43, "Angola": 42, "Bulgaria": 42, "El Salvador": 41, "Namibia": 41,
    "Suriname": 41, "Mongolia": 40, "Vanuatu": 39, "Panama": 39, "Tajikistan": 38,
    "Dominican Republic": 38, "Equatorial Guinea": 38, "Antigua and Barbuda": 38,
    "Guyana": 37, "Bahrain": 37, "North Korea": 37, "Moldova": 36, "Guatemala": 35,
    "Paraguay": 34, "Rwanda": 34, "Saint Lucia": 34, "Djibouti": 33,
    "Pakistan": 33, "Saint Kitts and Nevis": 32, "Turkey": 32, "Guinea-Bissau": 32,
    "Dominica": 32, "Palau": 31, "Vatican City": 31, "Georgia": 30, "Bahamas": 30,
    "Samoa": 30, "Madagascar": 30, "Russia": 29, "Kiribati": 28, "Haiti": 28,
    "Sri Lanka": 28, "Central African Republic": 28, "Benin": 28,
    "Republic of the Congo": 28, "Belarus": 27, "Eswatini": 27,
    "Trinidad and Tobago": 26, "Papua New Guinea": 26, "Myanmar": 25,
    "Armenia": 25, "Bangladesh": 25, "Niger": 24, "Tuvalu": 24, "Gabon": 23,
    "Ivory Coast": 23, "Solomon Islands": 23, "Kyrgyzstan": 22, "Grenada": 22,
    "Kazakhstan": 22, "Kenya": 21, "Democratic Republic of the Congo": 21,
    "Jamaica": 21, "Azerbaijan": 20, "Uzbekistan": 20, "Syria": 18,
    "Palestine": 18, "Turkmenistan": 18, "Comoros": 18, "Malaysia": 18,
    "Jordan": 17, "Liberia": 16, "Lebanon": 16,
    "Saint Vincent and the Grenadines": 16, "Ghana": 15, "Chad": 15, "Guinea": 14,
    "Tunisia": 14, "Tanzania": 14, "Sudan": 14, "Sierra Leone": 13, "Libya": 13,
    "Saudi Arabia": 13, "Algeria": 13, "Morocco": 13, "Iraq": 13,
    "Indonesia": 12, "Zimbabwe": 12, "Ethiopia": 12, "United Arab Emirates": 11,
    "Nigeria": 11, "Yemen": 10, "Mauritania": 10, "Egypt": 10, "Burundi": 10,
    "Uganda": 9, "Tonga": 9, "Togo": 9, "Burkina Faso": 9, "Malawi": 8,
    "Zambia": 8, "Qatar": 8, "Mali": 8, "Cameroon": 7, "South Sudan": 7,
    "Eritrea": 7, "Maldives": 6, "Kuwait": 6, "Iran": 5, "Senegal": 4,
    "Oman": 3, "Gambia": 3, "Brunei": 3, "Afghanistan": 1, "Somalia": 0,
}

# ── Canonical name → Equaldex name (where they differ) ───────────────────────
# UK home nations all share the United Kingdom entry on Equaldex
CANONICAL_TO_EQUALDEX: dict[str, str] = {
    "Türkiye":          "Turkey",
    "England":          "United Kingdom",
    "Scotland":         "United Kingdom",
    "Wales":            "United Kingdom",
    "Northern Ireland": "United Kingdom",
    "Congo DR":         "Democratic Republic of the Congo",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}

# ── Overrides: use another country's equality score ───────────────────────────
# Curaçao is a constituent country of the Kingdom of the Netherlands
EQUALITY_OVERRIDES: dict[str, str] = {
    "Curaçao": "Netherlands",
}

# ── FIFA name → canonical name (normalise to match teams.csv / common usage) ─
FIFA_TO_CANONICAL: dict[str, str] = {
    "USA":                          "United States",
    "IR Iran":                      "Iran",
    "Korea Republic":               "South Korea",
    "Korea DPR":                    "North Korea",
    "Turkey":                       "Türkiye",
    "Cabo Verde":                   "Cape Verde",
    "Bosnia and Herzegovina":       "Bosnia-Herzegovina",
    "Congo DR":                     "Congo DR",          # already correct
    "Côte d'Ivoire":                "Ivory Coast",
    "Kyrgyz Republic":              "Kyrgyzstan",
    "Republic of Ireland":          "Ireland",
    "Congo":                        "Republic of the Congo",
    "São Tomé and Príncipe":        "Sao Tome and Principe",
    "Brunei Darussalam":            "Brunei",
    "China PR":                     "China",
    "St Kitts and Nevis":           "Saint Kitts and Nevis",
    "St Lucia":                     "Saint Lucia",
    "St Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "The Gambia":                   "Gambia",
}

# ── Full FIFA rankings (April 1, 2026 — 211 teams) ────────────────────────────
FIFA_RANKINGS: list[tuple[int, str]] = [
    (1, "France"), (2, "Spain"), (3, "Argentina"), (4, "England"),
    (5, "Portugal"), (6, "Brazil"), (7, "Netherlands"), (8, "Morocco"),
    (9, "Belgium"), (10, "Germany"), (11, "Croatia"), (12, "Italy"),
    (13, "Colombia"), (14, "Senegal"), (15, "Mexico"), (16, "USA"),
    (17, "Uruguay"), (18, "Japan"), (19, "Switzerland"), (20, "Denmark"),
    (21, "IR Iran"), (22, "Turkey"), (23, "Ecuador"), (24, "Austria"),
    (25, "Korea Republic"), (26, "Nigeria"), (27, "Australia"), (28, "Algeria"),
    (29, "Egypt"), (30, "Canada"), (31, "Norway"), (32, "Ukraine"),
    (33, "Panama"), (34, "Côte d'Ivoire"), (35, "Poland"), (36, "Russia"),
    (37, "Wales"), (38, "Sweden"), (39, "Serbia"), (40, "Paraguay"),
    (41, "Czechia"), (42, "Hungary"), (43, "Scotland"), (44, "Tunisia"),
    (45, "Cameroon"), (46, "Congo DR"), (47, "Greece"), (48, "Slovakia"),
    (49, "Venezuela"), (50, "Uzbekistan"), (51, "Costa Rica"), (52, "Mali"),
    (53, "Peru"), (54, "Chile"), (55, "Qatar"), (56, "Romania"), (57, "Iraq"),
    (58, "Slovenia"), (59, "Republic of Ireland"), (60, "South Africa"),
    (61, "Saudi Arabia"), (62, "Burkina Faso"), (63, "Jordan"), (64, "Albania"),
    (65, "Bosnia and Herzegovina"), (66, "Honduras"), (67, "North Macedonia"),
    (68, "United Arab Emirates"), (69, "Cabo Verde"), (70, "Northern Ireland"),
    (71, "Jamaica"), (72, "Georgia"), (73, "Finland"), (74, "Ghana"),
    (75, "Iceland"), (76, "Bolivia"), (77, "Israel"), (78, "Kosovo"),
    (79, "Oman"), (80, "Guinea"), (81, "Montenegro"), (82, "Curaçao"),
    (83, "Haiti"), (84, "Syria"), (85, "New Zealand"), (86, "Bulgaria"),
    (87, "Gabon"), (88, "Uganda"), (89, "Angola"), (90, "Benin"),
    (91, "Bahrain"), (92, "Zambia"), (93, "Thailand"), (94, "China PR"),
    (95, "Palestine"), (96, "Guatemala"), (97, "Belarus"), (98, "Luxembourg"),
    (99, "Vietnam"), (100, "El Salvador"), (101, "Mozambique"),
    (102, "Trinidad and Tobago"), (103, "Tajikistan"), (104, "Madagascar"),
    (105, "Equatorial Guinea"), (106, "Armenia"), (107, "Kyrgyz Republic"),
    (108, "Lebanon"), (109, "Comoros"), (110, "Kazakhstan"), (111, "Kenya"),
    (112, "Libya"), (113, "Tanzania"), (114, "Niger"), (115, "Mauritania"),
    (116, "The Gambia"), (117, "Sudan"), (118, "Korea DPR"), (119, "Sierra Leone"),
    (120, "Namibia"), (121, "Togo"), (122, "Indonesia"), (123, "Faroe Islands"),
    (124, "Azerbaijan"), (125, "Suriname"), (126, "Cyprus"), (127, "Malawi"),
    (128, "Rwanda"), (129, "Estonia"), (130, "Zimbabwe"), (131, "Nicaragua"),
    (132, "Guinea-Bissau"), (133, "Congo"), (134, "Kuwait"), (135, "Philippines"),
    (136, "India"), (137, "Latvia"), (138, "Malaysia"), (139, "Central African Republic"),
    (140, "Liberia"), (141, "Turkmenistan"), (142, "Burundi"),
    (143, "Dominican Republic"), (144, "Ethiopia"), (145, "Lesotho"),
    (146, "Botswana"), (147, "Singapore"), (148, "Lithuania"), (149, "Yemen"),
    (150, "Guyana"), (151, "New Caledonia"), (152, "St Kitts and Nevis"),
    (153, "Solomon Islands"), (154, "Fiji"), (155, "Hong Kong, China"),
    (156, "Puerto Rico"), (157, "Tahiti"), (158, "Myanmar"), (159, "Moldova"),
    (160, "Vanuatu"), (161, "Malta"), (162, "Antigua and Barbuda"), (163, "Grenada"),
    (164, "Cuba"), (165, "Eswatini"), (166, "Bermuda"), (167, "St Lucia"),
    (168, "Papua New Guinea"), (169, "Afghanistan"), (170, "South Sudan"),
    (171, "St Vincent and the Grenadines"), (172, "Maldives"), (173, "Andorra"),
    (174, "Chinese Taipei"), (175, "Montserrat"), (176, "Nepal"), (177, "Cambodia"),
    (178, "Mauritius"), (179, "Barbados"), (180, "Belize"), (181, "Bangladesh"),
    (182, "Dominica"), (183, "Chad"), (184, "Eritrea"), (185, "Laos"),
    (186, "Bhutan"), (187, "Mongolia"), (188, "Cook Islands"), (189, "Aruba"),
    (190, "Samoa"), (191, "Sri Lanka"), (192, "American Samoa"),
    (193, "Brunei Darussalam"), (194, "Macau"), (195, "Cayman Islands"),
    (196, "São Tomé and Príncipe"), (197, "Djibouti"), (198, "Somalia"),
    (199, "Tonga"), (200, "Timor-Leste"), (201, "Guam"), (202, "Pakistan"),
    (203, "Gibraltar"), (204, "Seychelles"), (205, "Turks and Caicos Islands"),
    (206, "Liechtenstein"), (207, "Bahamas"), (208, "British Virgin Islands"),
    (209, "US Virgin Islands"), (210, "Anguilla"), (211, "San Marino"),
]


def fetch_fifa_rankings() -> list[tuple[int, str]] | None:
    """Try to fetch live rankings from inside.fifa.com. Returns None on failure."""
    try:
        import urllib.request, json, re
        url = "https://inside.fifa.com/fifa-world-ranking/men"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Look for embedded JSON ranking data (FIFA embeds __NEXT_DATA__ or similar)
        match = re.search(r'"rankings"\s*:\s*(\[.*?\])', html, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group(1))
        return [(int(item["rank"]), item["name"]) for item in data]
    except Exception:
        return None


def build() -> pd.DataFrame:
    rankings = fetch_fifa_rankings()
    if rankings:
        print("Using live FIFA rankings from inside.fifa.com")
    else:
        print("Live fetch failed or page is JS-rendered — using hardcoded April 1, 2026 data")
        rankings = FIFA_RANKINGS

    rows = []
    for rank, fifa_name in rankings:
        canonical = FIFA_TO_CANONICAL.get(fifa_name, fifa_name)

        # Resolve equality score: check overrides first, then canonical→equaldex map, then direct
        if canonical in EQUALITY_OVERRIDES:
            eq_key = EQUALITY_OVERRIDES[canonical]
        else:
            eq_key = CANONICAL_TO_EQUALDEX.get(canonical, canonical)

        equality = EQUALITY_INDEX.get(eq_key)

        rows.append({
            "country":        canonical,
            "fifa_ranking":   rank,
            "equality_index": equality,  # None if not found
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build()
    out = Path(__file__).parent.parent / "data" / "rankings.csv"
    df.to_csv(out, index=False)
    matched = df["equality_index"].notna().sum()
    print(f"Written {len(df)} teams to {out}")
    print(f"Equality index matched: {matched}/{len(df)}")
    missing = df[df["equality_index"].isna()]["country"].tolist()
    if missing:
        print(f"No equality data for: {', '.join(missing)}")
