import streamlit as st
import pandas as pd
from utils.team import CATEGORIES
from utils import fantasy


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


def show_players(player_map, team_map):
    # col1, col2, col3 = st.columns(3)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧍 Player Stats (total)")
    with col2:
        player_view = st.radio("View:", ["Stats", "Z-Scores"], key="player_view", horizontal=True)
    # with col3:
        # team1_name = st.selectbox("stats splits", STATS_TYPES, key="jonah")

    player_rows = []
    for p in player_map.values():
        ownership = (
            team_map[p.on_team_id].name if p.on_team_id in team_map
            else ("FA" if p.status == "FREEAGENT" else "WAIVER")
        )
        base = {
            "Name": p.name,
            "Ownership": ownership,
            "Pro Team": p.pro_team,
            "Pos": p.position,
            "Score": round(p.stats_z["total"].get("score", 0), 2)
        }
        cats = CATEGORIES
        src = p.stats_z if player_view == "Z-Scores" else p.stats
        for cat in cats:
            val = src["total"].get(cat, 0)
            base[cat] = round_value(cat, val, player_view == "Z-Scores")
        base["ROS%"] = round(p.percent_owned, 1)
        player_rows.append(base)

    player_df = pd.DataFrame(player_rows)
    st.dataframe(player_df, width='stretch', height=len(player_df) * 35 + 38)


def show_teams(team_map, counting_stats, roster_size, trade):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏢 Team Stats (total)")
    with col2:
        team_view = st.radio("View:", ["Total", "Average", "Z-Scores"], key=f"team_view{trade}", horizontal=True)

    team_rows = []
    for t in team_map.values():
        base = {
            "Team": t.name,
            "Abbrev": t.team_abbrev,
            "Score": round(t.stats_z["total"].get("score", 0), 2)
        }
        src = t.stats_z if team_view == "Z-Scores" else t.stats
        for cat in CATEGORIES:
            val = src["total"].get(cat, 0)
            if team_view == "Average" and cat in counting_stats:
                val = val / roster_size
            base[cat] = round_value(cat, val, team_view == "Z-Scores")
        team_rows.append(base)

    team_df = pd.DataFrame(team_rows)
    st.dataframe(team_df, width='stretch')


def show_standings(team_map, trade):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 League Standings")
    with col2:
        stand_view = st.radio("View:", ["H2H Most", "H2H Each"], key=f"stand_view{trade}", horizontal=True)

    if stand_view == "H2H Most":
        df = make_h2h_most_df(team_map).sort_values("win%", ascending=False)
    else:
        df = make_h2h_each_df(team_map).sort_values("win%", ascending=False)
    st.dataframe(df, width='stretch')


def show_roster(team_map, player_map):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧢 Team Roster Viewer")
    with col2:
        roster_view = st.radio("View:", ["Stats", "Z-Scores"], key="roster_view", horizontal=True)
    view = roster_view

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


# --- Helper: Compute Totals, Averages, and Differences ---
def totals_and_avg(plus_info, minus_info, counting_stats):
    stype = "total"
    plus_total = plus_info[stype]["total"]
    minus_total = minus_info[stype]["total"]
    

    # --- Compute Averages ---
    plus_avg = {}
    minus_avg = {}
    
    # Handle division-by-zero for averages
    plus_size = max(1, plus_info["size"])
    minus_size = max(1, minus_info["size"])

    for k, v in plus_total.items():
        if k in counting_stats:
            plus_avg[k] = round(v / plus_size, 1)
            plus_total[k] = round(plus_total.get(k), 1)
        else:
            plus_avg[k] = round(v, 3)
            plus_total[k] = round(plus_total.get(k), 3)

    for k, v in minus_total.items():
        if k in counting_stats:
            minus_avg[k] = round(v / minus_size, 1)
            minus_total[k] = round(minus_total.get(k), 1)
        else:
            minus_avg[k] = round(v, 3)
            minus_total[k] = round(minus_total.get(k), 3)
        
        
    total_df = pd.DataFrame([plus_total, minus_total], index=["Gained", "Lost"])
    diff_df = pd.DataFrame([total_df.iloc[0] - total_df.iloc[1]], index=["Diff"])

    avg_df = pd.DataFrame([plus_avg, minus_avg], index=["Gained", "Lost"])
    diff_avg_df = pd.DataFrame([avg_df.iloc[0] - avg_df.iloc[1]], index=["Diff"])
    
    return total_df, diff_df, avg_df, diff_avg_df


# --- Helper function to render compact player list ---
def render_player_list(players, trade_actions, options, key_prefix):
    for p in players:
        cols = st.columns([3, 2])
        with cols[0]:
            st.markdown(f"**{p.name}** ({p.position})")
        with cols[1]:
            action = st.selectbox(
                " ",
                options,
                key=f"{key_prefix}_{p.player_id}",
                label_visibility="collapsed"
            )
        if action:
            trade_actions[p.player_id] = action


# --- Helper: Convert info dict to DataFrame ---
def transaction_to_df(player_map, info, mode):
    stype = "total"
    rows = []
    for pid in info[stype]:
        if pid == "total":  # skip total entry
            continue
        p = player_map.get(pid)
        data = p.stats_z if mode == "📈 Z-Scores" else p.stats
        data = data.get(stype, {})
        row = {"Player": p.name}
        for cat in CATEGORIES:
            val = data.get(cat, 0)
            if cat in ["FG%", "FT%"]:
                row[cat] = round(val, 3)
            else:
                row[cat] = round(val, 1)
        rows.append(row)
    return pd.DataFrame(rows)


def show_trade(team_map, player_map, free_agents_map, counting_stats, percentage_stats, categories, cat_index, mask, roster_size):
    st.subheader("💼 Trade Analyzer")
    col1, col2, col3 = st.columns(3)
    # --- Team selectors ---

    team_names = [t.name for t in team_map.values()]
    with col1:
        team1_name = st.selectbox("Select Team 1", team_names, key="trade_team1")

    with col2:
        team2_name = st.selectbox("Select Team 2", [n for n in team_names if n != team1_name], key="trade_team2")

    team1 = next(t for t in team_map.values() if t.name == team1_name)
    team2 = next(t for t in team_map.values() if t.name == team2_name)
    with col3:
        # --- Limit how many free agents to show ---
        fa_limit = st.selectbox(
            "How many free agents/waivers to show?",
            [15, 30, 50, 100],
            index=0,
            key="fa_limit"
        )

    # --- Get players from each team and free agents ---
    players_team1 = [p for p in player_map.values() if p.on_team_id == team1.team_id]
    players_team2 = [p for p in player_map.values() if p.on_team_id == team2.team_id]
    players_free = [p for p in free_agents_map.values()][:fa_limit]

    # --- Display three columns ---
    col1, col2, col3 = st.columns(3)
    trade_actions = {}


    # --- Team 1 players ---
    with col1:
        st.markdown(f"### {team1_name}")
        render_player_list(players_team1, trade_actions, ["", "TRADE", "DROP"], "t1")

    # --- Team 2 players ---
    with col2:
        st.markdown(f"### {team2_name}")
        render_player_list(players_team2, trade_actions, ["", "TRADE", "DROP"], "t2")

    # --- Free Agents / Waivers ---
    with col3:
        st.markdown("### Free Agents / Waivers")
        for p in players_free:
            cols = st.columns([3, 2])
            status = "WAIVER" if getattr(p, "status", "").upper() == "WAIVERS" else ""
            with cols[0]:
                st.markdown(f"**{p.name}** ({p.position}) {status}")
            with cols[1]:
                action = st.selectbox(
                    " ",
                    ["", f"to {team1_name}", f"to {team2_name}"],
                    key=f"free_{p.player_id}",
                    label_visibility="collapsed"
                )
            if action:
                trade_actions[p.player_id] = action


    # --- Persistent state for Streamlit ---
    if "trade_result" not in st.session_state:
        st.session_state.trade_result = None
    if "trade_view" not in st.session_state:
        st.session_state.trade_view = "📊 Stats"

    # --- Analyze Button ---
    if st.button("🔍 Analyze Trade"):
        trade_dict = {}
        result = {'plus': [], 'minus': []}

        for pid, action in trade_actions.items():
            player = player_map[pid]

            if action == "TRADE":
                if player.on_team_id == team1.team_id:
                    trade_dict[pid] = team2.team_id
                    result["minus"].append(pid)
                elif player.on_team_id == team2.team_id:
                    trade_dict[pid] = team1.team_id
                    result["plus"].append(pid)
            elif action == "DROP":
                trade_dict[pid] = 0
                result["minus"].append(pid)
            elif "to" in action:
                if team1_name in action:
                    trade_dict[pid] = team1.team_id
                    result["plus"].append(pid)
                elif team2_name in action:
                    trade_dict[pid] = team2.team_id
                    result["minus"].append(pid)

        st.session_state.trade_result = (result, trade_dict)

    # --- Only render if we have a stored trade result ---
    if st.session_state.trade_result:
        result, trade_dict = st.session_state.trade_result

        # st.markdown("### 📦 Proposed Trade Dictionary")
        # st.json(trade_dict)

        # Use your compute logic
        plus, minus = fantasy.analyze_transaction(
            result, trade_dict, player_map, team_map,
            counting_stats, percentage_stats,
            categories, cat_index, mask, roster_size
        )

        # --- Display in a single row (side-by-side layout) ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💼 Trade Comparison")
        with col2:
            # Switch view (persistent, doesn’t reset page)
            st.session_state.trade_view = st.radio(
                "Select View Mode:",
                ["📊 Stats", "📈 Z-Scores"],
                horizontal=True,
                key="trade_view_radio"
            )

        view_mode = st.session_state.trade_view
        plus_df = transaction_to_df(player_map, plus, view_mode)
        minus_df = transaction_to_df(player_map, minus, view_mode)

        total_df, diff_df, avg_df, diff_avg_df = totals_and_avg(plus, minus, counting_stats)

        st.markdown(f"#### ⬆️ Players Gained ({team1_name})")
        st.dataframe(plus_df, width='stretch')
        st.markdown(f"#### ⬇️ Players Lost ({team1_name})")
        st.dataframe(minus_df, width='stretch')
        

        st.markdown("### 📊 Trade Summary (Totals)")
        st.dataframe(total_df, width='stretch')
        st.dataframe(diff_df, width='stretch')

        st.markdown("### 📊 Trade Summary (Averages)")
        st.dataframe(avg_df, width='stretch')
        st.dataframe(diff_avg_df, width='stretch')


        show_standings(team_map, '_t')
        show_teams(team_map, counting_stats, roster_size, '_t')
