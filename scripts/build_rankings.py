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

# ── Live FIFA rankings (June 10, 2026 — 211 teams) — rank, name, elo points ───
FIFA_RANKINGS: list[tuple[int, str, float]] = [
    (1, "Argentina", 1876.12), (2, "Spain", 1874.71), (3, "France", 1870.70),
    (4, "England", 1827.05), (5, "Portugal", 1766.18), (6, "Brazil", 1765.86),
    (7, "Morocco", 1755.10), (8, "Netherlands", 1753.57), (9, "Belgium", 1742.24),
    (10, "Germany", 1735.77), (11, "Croatia", 1714.87), (12, "Italy", 1704.73),
    (13, "Colombia", 1698.35), (14, "Mexico", 1687.48), (15, "Senegal", 1684.07),
    (16, "Uruguay", 1673.07), (17, "USA", 1671.23), (18, "Japan", 1661.58),
    (19, "Switzerland", 1650.06), (20, "IR Iran", 1619.58), (21, "Denmark", 1619.47),
    (22, "Türkiye", 1605.73), (23, "Ecuador", 1598.52), (24, "Austria", 1597.40),
    (25, "Korea Republic", 1591.63), (26, "Nigeria", 1586.69), (27, "Australia", 1579.34),
    (28, "Algeria", 1571.03), (29, "Egypt", 1562.37), (30, "Canada", 1559.48),
    (31, "Norway", 1557.44), (32, "Ukraine", 1549.29), (33, "Côte d'Ivoire", 1540.87),
    (34, "Panama", 1539.16), (35, "Russia", 1529.60), (36, "Poland", 1526.18),
    (37, "Wales", 1516.95), (38, "Sweden", 1509.79), (39, "Hungary", 1506.39),
    (40, "Czechia", 1505.74), (41, "Paraguay", 1505.35), (42, "Scotland", 1503.34),
    (43, "Serbia", 1502.13), (44, "Cameroon", 1481.24), (45, "Tunisia", 1476.41),
    (46, "Congo DR", 1474.43), (47, "Slovakia", 1473.66), (48, "Greece", 1473.19),
    (49, "Venezuela", 1464.30), (50, "Uzbekistan", 1458.73), (51, "Chile", 1458.20),
    (52, "Peru", 1457.69), (53, "Costa Rica", 1457.00), (54, "Romania", 1455.89),
    (55, "Mali", 1455.59), (56, "Iraq", 1451.15), (57, "Qatar", 1450.31),
    (58, "Republic of Ireland", 1441.10), (59, "Slovenia", 1441.09),
    (60, "South Africa", 1428.38), (61, "Saudi Arabia", 1423.88),
    (62, "Burkina Faso", 1406.99), (63, "Jordan", 1387.74),
    (64, "Bosnia and Herzegovina", 1387.22), (65, "Honduras", 1378.97),
    (66, "Albania", 1376.03), (67, "Cabo Verde", 1371.11),
    (68, "United Arab Emirates", 1370.47), (69, "North Macedonia", 1369.16),
    (70, "Northern Ireland", 1365.30), (71, "Jamaica", 1357.84),
    (72, "Georgia", 1355.26), (73, "Ghana", 1346.88), (74, "Iceland", 1343.92),
    (75, "Finland", 1341.92), (76, "Israel", 1333.90), (77, "Bolivia", 1326.00),
    (78, "Kosovo", 1319.12), (79, "Oman", 1306.90), (80, "Montenegro", 1301.98),
    (81, "Guinea", 1295.60), (82, "Curaçao", 1294.77), (83, "Haiti", 1293.10),
    (84, "Syria", 1283.05), (85, "New Zealand", 1275.58), (86, "Gabon", 1272.51),
    (87, "Bulgaria", 1271.68), (88, "Angola", 1265.58), (89, "Uganda", 1264.09),
    (90, "Zambia", 1255.82), (91, "China PR", 1254.81), (92, "Bahrain", 1254.41),
    (93, "Benin", 1252.17), (94, "Thailand", 1250.80), (95, "Palestine", 1243.71),
    (96, "Belarus", 1242.88), (97, "Guatemala", 1238.74), (98, "Luxembourg", 1232.82),
    (99, "Vietnam", 1225.68), (100, "El Salvador", 1225.34), (101, "Tajikistan", 1224.19),
    (102, "Trinidad and Tobago", 1219.59), (103, "Mozambique", 1218.62),
    (104, "Madagascar", 1202.69), (105, "Equatorial Guinea", 1195.20),
    (106, "Kyrgyz Republic", 1192.16), (107, "Armenia", 1189.63),
    (108, "Comoros", 1187.91), (109, "Kenya", 1185.08), (110, "Libya", 1182.08),
    (111, "Kazakhstan", 1180.78), (112, "Tanzania", 1180.27),
    (113, "Mauritania", 1176.68), (114, "Niger", 1175.33), (115, "Lebanon", 1172.22),
    (116, "The Gambia", 1159.64), (117, "Sudan", 1157.22), (118, "Indonesia", 1157.14),
    (119, "Togo", 1152.76), (120, "Korea DPR", 1151.05), (121, "Namibia", 1148.84),
    (122, "Sierra Leone", 1147.56), (123, "Faroe Islands", 1136.59),
    (124, "Cyprus", 1133.25), (125, "Suriname", 1132.43), (126, "Azerbaijan", 1132.00),
    (127, "Estonia", 1130.64), (128, "Rwanda", 1126.62), (129, "Malawi", 1122.05),
    (130, "Zimbabwe", 1119.78), (131, "Nicaragua", 1114.63),
    (132, "Guinea-Bissau", 1108.38), (133, "Kuwait", 1106.47), (134, "Congo", 1105.96),
    (135, "Philippines", 1100.95), (136, "Malaysia", 1086.22), (137, "Latvia", 1085.66),
    (138, "India", 1084.93), (139, "Central African Republic", 1080.82),
    (140, "Liberia", 1080.44), (141, "Turkmenistan", 1078.65), (142, "Burundi", 1078.01),
    (143, "Ethiopia", 1077.52), (144, "Dominican Republic", 1076.50),
    (145, "Yemen", 1065.24), (146, "Lesotho", 1064.29), (147, "Botswana", 1063.63),
    (148, "Singapore", 1057.95), (149, "Lithuania", 1056.85), (150, "Guyana", 1049.32),
    (151, "New Caledonia", 1036.95), (152, "St Kitts and Nevis", 1036.33),
    (153, "Solomon Islands", 1031.89), (154, "Puerto Rico", 1024.30),
    (155, "Fiji", 1024.17), (156, "Hong Kong, China", 1024.16), (157, "Tahiti", 1019.04),
    (158, "Myanmar", 1010.91), (159, "Moldova", 1008.24), (160, "Vanuatu", 1002.53),
    (161, "Malta", 992.79), (162, "Antigua and Barbuda", 986.58), (163, "Grenada", 981.82),
    (164, "Cuba", 981.42), (165, "Eswatini", 979.01), (166, "St Lucia", 976.71),
    (167, "Bermuda", 975.05), (168, "Papua New Guinea", 974.90),
    (169, "Afghanistan", 971.20), (170, "South Sudan", 970.94),
    (171, "St Vincent and the Grenadines", 968.27), (172, "Andorra", 946.43),
    (173, "Maldives", 943.92), (174, "Chinese Taipei", 923.78),
    (175, "Cambodia", 922.32), (176, "Montserrat", 916.75), (177, "Nepal", 914.54),
    (178, "Mauritius", 911.49), (179, "Barbados", 909.89), (180, "Belize", 907.00),
    (181, "Bangladesh", 902.93), (182, "Dominica", 897.69), (183, "Chad", 896.85),
    (184, "Eritrea", 887.06), (185, "Laos", 885.03), (186, "Cook Islands", 877.53),
    (187, "Sri Lanka", 876.86), (188, "Samoa", 876.41), (189, "Aruba", 875.61),
    (190, "Mongolia", 874.47), (191, "American Samoa", 871.61), (192, "Bhutan", 870.81),
    (193, "Macau", 858.03), (194, "Brunei Darussalam", 857.73),
    (195, "São Tomé and Príncipe", 855.44), (196, "Djibouti", 853.58),
    (197, "Cayman Islands", 850.06), (198, "Somalia", 839.17), (199, "Pakistan", 837.15),
    (200, "Tonga", 835.64), (201, "Timor-Leste", 831.00), (202, "Gibraltar", 820.26),
    (203, "Guam", 819.54), (204, "Seychelles", 804.16),
    (205, "Turks and Caicos Islands", 803.98), (206, "Liechtenstein", 797.70),
    (207, "Bahamas", 786.82), (208, "US Virgin Islands", 779.76),
    (209, "British Virgin Islands", 777.41), (210, "Anguilla", 760.25),
    (211, "San Marino", 721.20),
]


def build() -> pd.DataFrame:
    print("Using hardcoded June 10, 2026 data from inside.fifa.com")
    rows = []
    for rank, fifa_name, points in FIFA_RANKINGS:
        canonical = FIFA_TO_CANONICAL.get(fifa_name, fifa_name)

        if canonical in EQUALITY_OVERRIDES:
            eq_key = EQUALITY_OVERRIDES[canonical]
        else:
            eq_key = CANONICAL_TO_EQUALDEX.get(canonical, canonical)

        equality = EQUALITY_INDEX.get(eq_key)

        rows.append({
            "country":        canonical,
            "fifa_ranking":   rank,
            "fifa_points":    points,
            "equality_index": equality,
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
