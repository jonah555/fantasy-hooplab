import streamlit as st
import pandas as pd
from utils.team import CATEGORIES


def round_value(cat, val, is_z=False):
    """Consistent rounding and formatting for roster view."""
    if is_z:
        return round(val, 2)
    if cat == "MIN":
        return int(round(val))
    if cat in ["FG%", "FT%"]:
        return round(val, 3)
    return f"{val:.1f}"


def make_h2h_most_df(team_map):
    """Return DataFrame showing W-L-T and Win% for each team."""
    rows = []
    for t in team_map.values():
        h2h = t.h2h_most.get("total", {})
        result = h2h.get("result", "0-0-0")
        winpct = h2h.get("win%", 0)
        rows.append({
            "Team": t.name,
            "Record": result,
            "win%": round(winpct, 3),
        })
    df = pd.DataFrame(rows)
    return df


def make_h2h_each_df(team_map):
    """Return per-category W-L-T and Win% for each team."""
    rows = []
    for t in team_map.values():
        h2h = t.h2h_each.get("total", {})
        row = {
            "Team": t.name,
            "Record": h2h.get("result", "0-0-0"),
            "win%": round(h2h.get("win%", 0), 3),
        }
        for cat in CATEGORIES:
            wlt = h2h.get(cat, [0, 0, 0])
            row[cat] = f"{wlt[0]}-{wlt[1]}-{wlt[2]}"
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def show_team_roster(team_map, player_map, view="Stats"):
    """Display one team's roster with Stats or Z-Scores view."""
    st.markdown("#### 📋 Select Team to View Roster")
    team_names = {t.name: t for t in team_map.values()}
    selected_name = st.selectbox("Select team:", list(team_names.keys()))
    team = team_names[selected_name]

    # Choose source
    is_z = view == "Z-Scores"
    stype = "total"

    roster_rows = []
    for pid in team.roster:
        player = player_map.get(pid)
        if not player:
            continue

        src = player.stats_z if is_z else player.stats
        base = {
            "Name": player.name,
            "Pro Team": player.pro_team,
            "Pos": player.position,
            "Score": round(player.stats_z[stype].get("score", 0), 2),
        }

        # add 9 categories with rounding
        for cat in ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]:
            val = src[stype].get(cat, 0)
            base[cat] = round_value(cat, val, is_z)

        roster_rows.append(base)

    roster_df = pd.DataFrame(roster_rows)
    st.dataframe(roster_df, width='stretch', height=len(roster_df) * 35 + 38)