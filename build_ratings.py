import json
import pandas as pd
from src.ratings import composite_rating

DATA = json.loads(r'''[{"team":"Mexico","elo":1868,"fifa_points":1684,"overall":77,"gk":76,"def":75,"mid":77,"att":78},{"team":"South Africa","elo":1517,"fifa_points":1429,"overall":73,"gk":67,"def":70,"mid":71,"att":73},{"team":"Korea Republic","elo":1756,"fifa_points":1590,"overall":77,"gk":75,"def":75,"mid":76,"att":78},{"team":"Czechia","elo":1733,"fifa_points":1503,"overall":76,"gk":78,"def":74,"mid":76,"att":77},{"team":"Canada","elo":1793,"fifa_points":1556,"overall":75,"gk":73,"def":76,"mid":73,"att":77},{"team":"Bosnia-Herzegovina","elo":1591,"fifa_points":1385,"overall":75,"gk":78,"def":74,"mid":74,"att":77},{"team":"Qatar","elo":1423,"fifa_points":1454,"overall":73,"gk":70,"def":68,"mid":69,"att":71},{"team":"Switzerland","elo":1894,"fifa_points":1651,"overall":79,"gk":87,"def":78,"mid":78,"att":82},{"team":"Brazil","elo":1763,"fifa_points":1761,"overall":84,"gk":89,"def":86,"mid":84,"att":85},{"team":"Morocco","elo":1757,"fifa_points":1756,"overall":80,"gk":82,"def":80,"mid":79,"att":80},{"team":"Haiti","elo":1530,"fifa_points":1294,"overall":69,"gk":69,"def":70,"mid":69,"att":70},{"team":"Scotland","elo":1500,"fifa_points":1498,"overall":78,"gk":72,"def":76,"mid":80,"att":75},{"team":"United States","elo":1676,"fifa_points":1673,"overall":80,"gk":79,"def":79,"mid":79,"att":80},{"team":"Paraguay","elo":1504,"fifa_points":1504,"overall":76,"gk":72,"def":75,"mid":76,"att":76},{"team":"Australia","elo":1579,"fifa_points":1581,"overall":72,"gk":68,"def":72,"mid":73,"att":70},{"team":"Turkiye","elo":1602,"fifa_points":1599,"overall":80,"gk":80,"def":79,"mid":81,"att":80},{"team":"Germany","elo":1925,"fifa_points":1730,"overall":84,"gk":88,"def":84,"mid":82,"att":80},{"team":"Curacao","elo":1433,"fifa_points":1310,"overall":68,"gk":70,"def":68,"mid":67,"att":66},{"team":"Ivory Coast","elo":1676,"fifa_points":1533,"overall":78,"gk":75,"def":78,"mid":80,"att":79},{"team":"Ecuador","elo":1935,"fifa_points":1595,"overall":76,"gk":75,"def":79,"mid":76,"att":73},{"team":"Netherlands","elo":1961,"fifa_points":1758,"overall":82,"gk":84,"def":84,"mid":83,"att":81},{"team":"Japan","elo":1906,"fifa_points":1660,"overall":77,"gk":78,"def":77,"mid":77,"att":79},{"team":"Sweden","elo":1714,"fifa_points":1515,"overall":78,"gk":78,"def":76,"mid":77,"att":87},{"team":"Tunisia","elo":1633,"fifa_points":1483,"overall":71,"gk":74,"def":72,"mid":72,"att":70},{"team":"Belgium","elo":1866,"fifa_points":1734.71,"overall":84,"gk":89,"def":82,"mid":86,"att":84},{"team":"Egypt","elo":1699,"fifa_points":1565.56,"overall":72,"gk":71,"def":71,"mid":70,"att":74},{"team":"Iran","elo":1764,"fifa_points":1616.04,"overall":74,"gk":75,"def":73,"mid":72,"att":77},{"team":"New Zealand","elo":1585,"fifa_points":1281,"overall":69,"gk":68,"def":68,"mid":70,"att":70},{"team":"Spain","elo":2165,"fifa_points":1876.4,"overall":85,"gk":85,"def":83,"mid":86,"att":85},{"team":"Cape Verde","elo":1576,"fifa_points":1366,"overall":71,"gk":69,"def":69,"mid":71,"att":70},{"team":"Saudi Arabia","elo":1566,"fifa_points":1421,"overall":71,"gk":72,"def":71,"mid":69,"att":72},{"team":"Uruguay","elo":1892,"fifa_points":1673.07,"overall":79,"gk":78,"def":78,"mid":79,"att":79},{"team":"France","elo":2081,"fifa_points":1877.32,"overall":87,"gk":87,"def":86,"mid":85,"att":85},{"team":"Senegal","elo":1866,"fifa_points":1686.41,"overall":79,"gk":80,"def":78,"mid":78,"att":79},{"team":"Iraq","elo":1608,"fifa_points":1447,"overall":63,"gk":64,"def":62,"mid":65,"att":66},{"team":"Norway","elo":1915,"fifa_points":1550.94,"overall":78,"gk":76,"def":75,"mid":78,"att":82},{"team":"Argentina","elo":2113,"fifa_points":1874.81,"overall":83,"gk":85,"def":80,"mid":84,"att":85},{"team":"Algeria","elo":1743,"fifa_points":1564.26,"overall":75,"gk":71,"def":75,"mid":77,"att":77},{"team":"Austria","elo":1828,"fifa_points":1593.45,"overall":77,"gk":72,"def":76,"mid":78,"att":79},{"team":"Jordan","elo":1685,"fifa_points":1391,"overall":67,"gk":66,"def":66,"mid":67,"att":67},{"team":"Portugal","elo":1984,"fifa_points":1763.83,"overall":85,"gk":84,"def":84,"mid":84,"att":85},{"team":"Congo DR","elo":1655,"fifa_points":1478.35,"overall":72,"gk":74,"def":73,"mid":72,"att":76},{"team":"Uzbekistan","elo":1718,"fifa_points":1465.34,"overall":66,"gk":70,"def":67,"mid":66,"att":65},{"team":"Colombia","elo":1977,"fifa_points":1693.09,"overall":79,"gk":79,"def":80,"mid":78,"att":79},{"team":"England","elo":2020,"fifa_points":1825.97,"overall":90,"gk":84,"def":82,"mid":82,"att":85},{"team":"Croatia","elo":1930,"fifa_points":1717.07,"overall":79,"gk":80,"def":78,"mid":79,"att":78},{"team":"Ghana","elo":1503,"fifa_points":1330,"overall":76,"gk":73,"def":73,"mid":74,"att":76},{"team":"Panama","elo":1733,"fifa_points":1539.14,"overall":70,"gk":72,"def":69,"mid":69,"att":69}]''')

df = pd.DataFrame(DATA)
df["player_overall"] = df["overall"]

R = composite_rating(df, {"elo": 0.5, "fifa": 0.2, "players": 0.3})

out = pd.DataFrame({
    "team": df["team"].values,
    "elo": df["elo"].values,
    "fifa_points": df["fifa_points"].values,
    "player_overall": df["player_overall"].values,
    "POR": df["gk"].values,
    "DEF": df["def"].values,
    "MED": df["mid"].values,
    "ATA": df["att"].values,
    "R": R.values,
})

out = out[["team", "elo", "fifa_points", "player_overall", "POR", "DEF", "MED", "ATA", "R"]]
path = "data/processed/ratings.csv"
out.to_csv(path, index=False, encoding="utf-8")

# Verification
chk = pd.read_csv(path)
print("ROWS:", len(chk))
print("ELO_NULLS:", int(chk["elo"].isnull().sum()))
top5 = chk.sort_values("R", ascending=False).head(5)
print("TOP5:")
for _, r in top5.iterrows():
    print(f"{r['team']}|{r['R']:.2f}")
