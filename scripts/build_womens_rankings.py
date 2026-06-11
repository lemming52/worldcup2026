"""Build data/womens_elo.csv from the FIFA/Coca-Cola Women's World Ranking.

Source: live ranking table at https://inside.fifa.com/fifa-world-ranking/women
(captured June 2026, includes pending match adjustments — 198 ranked teams).

Run from project root:
    python scripts/build_womens_rankings.py
"""

from pathlib import Path
import pandas as pd

# ── FIFA name → canonical name (normalise to match teams.csv / common usage) ─
FIFA_TO_CANONICAL: dict[str, str] = {
    "USA":                          "United States",
    "IR Iran":                      "Iran",
    "Korea Republic":               "South Korea",
    "Korea DPR":                    "North Korea",
    "Cabo Verde":                   "Cape Verde",
    "Bosnia and Herzegovina":       "Bosnia-Herzegovina",
    "Côte d'Ivoire":                "Ivory Coast",
    "Kyrgyz Republic":              "Kyrgyzstan",
    "Republic of Ireland":          "Ireland",
    "Congo":                        "Republic of the Congo",
    "China PR":                     "China",
    "St Kitts and Nevis":           "Saint Kitts and Nevis",
    "St Lucia":                     "Saint Lucia",
    "St Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "The Gambia":                   "Gambia",
}

# ── FIFA Women's World Ranking (June 2026, live — 198 teams) — rank, name, Elo points ─
WOMENS_FIFA_RANKINGS: list[tuple[int, str, float]] = [
    (1, "Spain", 2105.36), (2, "USA", 2057.92), (3, "Germany", 2028.99),
    (4, "England", 2027.13), (5, "Japan", 1998.83), (6, "France", 1983.84),
    (7, "Brazil", 1976.73), (8, "Sweden", 1937.94), (9, "Canada", 1936.90),
    (10, "Netherlands", 1911.75), (11, "Korea DPR", 1910.63), (12, "Denmark", 1910.20),
    (13, "Italy", 1891.83), (14, "Norway", 1878.52), (15, "Australia", 1830.66),
    (16, "China PR", 1799.13), (17, "Iceland", 1792.32), (18, "Belgium", 1786.01),
    (19, "Korea Republic", 1780.68), (20, "Colombia", 1775.96), (21, "Republic of Ireland", 1769.74),
    (22, "Portugal", 1751.11), (23, "Austria", 1749.66), (24, "Finland", 1744.99),
    (25, "Scotland", 1743.49), (26, "Switzerland", 1734.18), (27, "Russia", 1718.14),
    (28, "Mexico", 1715.13), (29, "Poland", 1694.17), (30, "Argentina", 1683.00),
    (31, "Wales", 1668.82), (32, "New Zealand", 1645.41), (33, "Czechia", 1641.00),
    (34, "Ukraine", 1634.21), (35, "Serbia", 1633.90), (36, "Nigeria", 1601.56),
    (37, "Vietnam", 1593.71), (38, "Slovenia", 1579.19), (39, "Philippines", 1566.44),
    (40, "Chinese Taipei", 1565.81), (41, "Jamaica", 1550.17), (42, "Venezuela", 1527.00),
    (43, "Costa Rica", 1523.57), (44, "Paraguay", 1511.01), (45, "Hungary", 1506.51),
    (46, "Türkiye", 1497.30), (47, "Haiti", 1490.83), (48, "Chile", 1487.00),
    (49, "Thailand", 1485.04), (50, "Northern Ireland", 1481.66), (51, "Uzbekistan", 1474.15),
    (52, "Belarus", 1473.09), (53, "Romania", 1472.28), (54, "Slovakia", 1467.43),
    (55, "Myanmar", 1460.70), (56, "Panama", 1457.45), (57, "South Africa", 1451.15),
    (58, "Papua New Guinea", 1450.33), (59, "Greece", 1430.17), (60, "Ghana", 1429.23),
    (61, "Ecuador", 1418.82), (62, "Uruguay", 1418.66), (63, "Croatia", 1406.00),
    (64, "Morocco", 1402.24), (65, "Zambia", 1390.14), (66, "Israel", 1382.64),
    (67, "Albania", 1376.23), (68, "IR Iran", 1370.37), (69, "India", 1368.70),
    (70, "Bosnia and Herzegovina", 1361.08), (71, "Cameroon", 1358.15), (72, "Côte d'Ivoire", 1338.92),
    (73, "Peru", 1331.32), (74, "Algeria", 1318.95), (75, "Azerbaijan", 1317.93),
    (76, "Jordan", 1299.21), (77, "Puerto Rico", 1294.95), (78, "El Salvador", 1294.40),
    (79, "Senegal", 1286.33), (80, "Fiji", 1282.20), (81, "Hong Kong, China", 1280.53),
    (82, "Trinidad and Tobago", 1269.08), (83, "Guatemala", 1267.25), (84, "Mali", 1263.53),
    (85, "Kosovo", 1262.78), (86, "Montenegro", 1250.20), (87, "Samoa", 1246.84),
    (88, "Nepal", 1238.74), (89, "Solomon Islands", 1234.03), (90, "Equatorial Guinea", 1229.60),
    (91, "Guyana", 1217.37), (92, "Malta", 1216.36), (93, "Dominican Republic", 1211.22),
    (94, "Lithuania", 1208.47), (95, "Malaysia", 1208.12), (96, "Nicaragua", 1205.13),
    (97, "Cuba", 1204.21), (98, "Guam", 1201.73), (99, "Egypt", 1199.25),
    (100, "Kazakhstan", 1199.11), (101, "Estonia", 1198.56), (102, "Tunisia", 1197.50),
    (103, "Faroe Islands", 1187.00), (104, "New Caledonia", 1184.36), (105, "Latvia", 1179.91),
    (106, "Congo DR", 1179.60), (107, "Bangladesh", 1171.05), (108, "Vanuatu", 1168.10),
    (109, "Bulgaria", 1166.44), (110, "Indonesia", 1162.58), (111, "Congo", 1161.03),
    (112, "Laos", 1153.73), (113, "Bolivia", 1153.64), (114, "Cambodia", 1153.44),
    (115, "Luxembourg", 1152.87), (116, "Tonga", 1152.53), (117, "Bahrain", 1146.97),
    (118, "Burkina Faso", 1140.68), (119, "Moldova", 1137.64), (120, "Cabo Verde", 1131.67),
    (121, "American Samoa", 1130.42), (122, "Tanzania", 1129.13), (123, "Tahiti", 1127.92),
    (124, "United Arab Emirates", 1126.67), (125, "Namibia", 1124.29), (126, "Honduras", 1115.28),
    (127, "Zimbabwe", 1114.75), (128, "Kenya", 1111.84), (129, "Palestine", 1111.40),
    (130, "Lebanon", 1100.95), (131, "Cook Islands", 1099.76), (132, "Georgia", 1098.68),
    (133, "Togo", 1092.99), (134, "The Gambia", 1082.47), (135, "Cyprus", 1076.22),
    (136, "North Macedonia", 1075.20), (137, "Kyrgyz Republic", 1070.63), (138, "Ethiopia", 1068.12),
    (139, "Benin", 1066.55), (140, "Suriname", 1065.77), (141, "Turkmenistan", 1063.88),
    (142, "Bermuda", 1053.17), (143, "Guinea", 1048.64), (144, "Central African Republic", 1045.87),
    (145, "Uganda", 1036.27), (146, "Mongolia", 1035.67), (147, "Armenia", 1030.03),
    (148, "Botswana", 1029.20), (149, "Gabon", 1028.74), (150, "St Kitts and Nevis", 1026.93),
    (151, "Singapore", 1025.38), (152, "Sierra Leone", 1021.39), (153, "Malawi", 1018.89),
    (154, "Pakistan", 1008.65), (155, "Angola", 989.68), (156, "Chad", 985.55),
    (157, "Timor-Leste", 965.35), (158, "Saudi Arabia", 960.38), (159, "Tajikistan", 954.78),
    (160, "St Vincent and the Grenadines", 947.14), (161, "Bhutan", 933.09), (162, "Syria", 931.42),
    (163, "Barbados", 924.87), (164, "St Lucia", 923.18), (165, "Sri Lanka", 915.58),
    (166, "Iraq", 910.49), (167, "Maldives", 906.97), (168, "Belize", 903.05),
    (169, "Rwanda", 892.39), (170, "Dominica", 884.73), (171, "Liberia", 882.37),
    (172, "Grenada", 878.19), (173, "Mozambique", 874.79), (174, "Niger", 863.94),
    (175, "Seychelles", 849.52), (176, "Macau", 846.53), (177, "Guinea-Bissau", 838.58),
    (178, "Lesotho", 836.43), (179, "Burundi", 822.10), (180, "Curaçao", 821.91),
    (181, "Andorra", 816.80), (182, "Antigua and Barbuda", 807.20), (183, "Aruba", 801.27),
    (184, "Eswatini", 797.06), (185, "US Virgin Islands", 790.28), (186, "Cayman Islands", 777.07),
    (187, "Comoros", 745.47), (188, "Libya", 739.94), (189, "Gibraltar", 734.15),
    (190, "Liechtenstein", 725.35), (191, "Madagascar", 724.45), (192, "Anguilla", 681.60),
    (193, "Bahamas", 665.71), (194, "Sudan", 628.74), (195, "South Sudan", 628.66),
    (196, "Turks and Caicos Islands", 627.14), (197, "Djibouti", 556.64), (198, "Mauritius", 433.66),
]


def build() -> pd.DataFrame:
    rows = []
    for rank, fifa_name, points in WOMENS_FIFA_RANKINGS:
        canonical = FIFA_TO_CANONICAL.get(fifa_name, fifa_name)
        rows.append({
            "country": canonical,
            "womens_fifa_ranking": rank,
            "womens_elo": points,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build()
    out = Path(__file__).parent.parent / "data" / "womens_elo.csv"
    df.to_csv(out, index=False)
    print(f"Written {len(df)} teams to {out}")

    teams = pd.read_csv(Path(__file__).parent.parent / "data" / "teams.csv")
    missing = sorted(set(teams["name"]) - set(df["country"]))
    if missing:
        print(f"No women's ranking data for: {', '.join(missing)} (model will use the fallback rating)")
