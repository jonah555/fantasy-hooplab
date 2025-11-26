import streamlit as st
import numpy as np
import pandas as pd
import espn_api.basketball as api
from utils import fantasy, render

YEAR = 2026
ROSTER_SIZE = 13
TEAM_COUNT = 10

# Categories (9CAT)
CATEGORIES = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
CAT_INDEX = np.arange(len(CATEGORIES))
COUNTING_STATS = ["PTS", "3PM", "REB", "AST", "STL", "BLK", "TO", "FGM", "FGA", "FTM", "FTA"]
PERCENTAGE_STATS = ["FG", "FT"]
NEGATIVE_STATS = ["TO"]
MASK = np.array([cat in NEGATIVE_STATS for cat in CATEGORIES])
STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]


st.set_page_config(page_title="Fantasy HoopLab", layout="wide")
st.title("🏀 Fantasy HoopLab")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Players", "Teams" ,"Standings", "Roster", "Trade"])

if "league" not in st.session_state:
    st.session_state.league = None
    st.session_state.team_map = None
    st.session_state.player_map = None
    st.session_state.free_agents_map = None
    st.session_state.top_players_map = None


# 1. HOME
with tab1:

    st.header("Home")
    league_id = st.text_input("League ID", value=816907987)
    fetch_btn = st.button("Fetch League Data")

    # --- Fetch League Data ---
    @st.cache_data(show_spinner="Connecting to ESPN Fantasy League...")
    def load_league_data(league_id, year, roster_size, team_count):
        league = api.League(league_id=league_id, year=year)
        team_map, player_map, free_agents_map, top_players_map = fantasy.get_roster(league, roster_size, team_count)
        return league, team_map, player_map, free_agents_map, top_players_map

    if fetch_btn:
        league, team_map, player_map, free_agents_map, top_players_map = load_league_data(
            league_id, YEAR, ROSTER_SIZE, TEAM_COUNT
        )

        st.session_state.league = league
        st.session_state.team_map = team_map
        st.session_state.player_map = player_map
        st.session_state.free_agents_map = free_agents_map
        st.session_state.top_players_map = top_players_map

        if league:
            st.write("Successfully connected to ESPN Fantasy League!")
            fantasy.compute_players_z_scores(player_map, top_players_map, CATEGORIES, CAT_INDEX, MASK)
            fantasy.compute_teams_z_scores(team_map, player_map, CATEGORIES, CAT_INDEX, MASK, COUNTING_STATS, PERCENTAGE_STATS, ROSTER_SIZE)
            for t in team_map.values():
                t.get_record(team_map, CATEGORIES)
        else:
            st.write("Please make sure your league is set to public or make sure league ID is correct.")

        st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. Players
with tab2:
    st.header("Players")
    if st.session_state.league:
        league = st.session_state.league
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        free_agents_map = st.session_state.free_agents_map
        top_players_map = st.session_state.top_players_map

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
                base[cat] = render.round_value(cat, val, player_view == "Z-Scores")
            base["ROS%"] = round(p.percent_owned, 1)
            player_rows.append(base)

        player_df = pd.DataFrame(player_rows)
        st.dataframe(player_df, width='stretch', height=len(player_df) * 35 + 38)
    else:
        st.write("Please return to Home Page and connect to your league.")
        

# 3. Teams
with tab3:
    st.header("Teams")
    if st.session_state.league:
        league = st.session_state.league
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        free_agents_map = st.session_state.free_agents_map
        top_players_map = st.session_state.top_players_map

        st.markdown("### 🏢 Team Stats (total)")
        team_view = st.radio("View:", ["Stats", "Z-Scores"], key="team_view", horizontal=True)

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
                base[cat] = render.round_value(cat, val, team_view == "Z-Scores")
            team_rows.append(base)

        team_df = pd.DataFrame(team_rows)
        st.dataframe(team_df, width='stretch')
    else:
        st.write("Please return to Home Page and connect to your league.")


# 4. Standings
with tab4:
    st.header("Standings")
    if st.session_state.league:
        league = st.session_state.league
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        free_agents_map = st.session_state.free_agents_map
        top_players_map = st.session_state.top_players_map

        st.markdown("### 🏆 League Standings")
        stand_view = st.radio("View:", ["H2H Most", "H2H Each"], key="stand_view", horizontal=True)

        if stand_view == "H2H Most":
            df = render.make_h2h_most_df(team_map).sort_values("win%", ascending=False)
        else:
            df = render.make_h2h_each_df(team_map).sort_values("win%", ascending=False)
        st.dataframe(df, width='stretch')
    else:
        st.write("Please return to Home Page and connect to your league.")


# 5. Roster
with tab5:
    st.header("Roster")
    if st.session_state.league:
        league = st.session_state.league
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        free_agents_map = st.session_state.free_agents_map
        top_players_map = st.session_state.top_players_map

        st.markdown("### 🧢 Team Roster Viewer")
        roster_view = st.radio("View:", ["Stats", "Z-Scores"], key="roster_view", horizontal=True)
        render.show_team_roster(team_map, player_map, view=roster_view)
    else:
        st.write("Please return to Home Page and connect to your league.")


# 6. Trade
with tab6:
    st.header("Trade")
    if st.session_state.league:
        league = st.session_state.league
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        free_agents_map = st.session_state.free_agents_map
        top_players_map = st.session_state.top_players_map
        
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

        # --- Helper function to render compact player list ---
        def render_player_list(players, team_label, options, key_prefix):
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


        # --- Team 1 players ---
        with col1:
            st.markdown(f"### {team1_name}")
            render_player_list(players_team1, team1_name, ["", "TRADE", "DROP"], "t1")

        # --- Team 2 players ---
        with col2:
            st.markdown(f"### {team2_name}")
            render_player_list(players_team2, team2_name, ["", "TRADE", "DROP"], "t2")

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
                COUNTING_STATS, PERCENTAGE_STATS,
                CATEGORIES, CAT_INDEX, MASK, ROSTER_SIZE
            )

            # Switch view (persistent, doesn’t reset page)
            st.session_state.trade_view = st.radio(
                "Select View Mode:",
                ["📊 Stats", "📈 Z-Scores"],
                horizontal=True,
                key="trade_view_radio"
            )

            view_mode = st.session_state.trade_view

            # --- Helper: Convert info dict to DataFrame ---
            def transaction_to_df(info, mode):
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

            plus_df = transaction_to_df(plus, view_mode)
            minus_df = transaction_to_df(minus, view_mode)

            # --- Helper: Compute Totals, Averages, and Differences ---
            def totals_and_avg(plus_info, minus_info):
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
                    if k in COUNTING_STATS:
                        plus_avg[k] = round(v / plus_size, 1)
                        plus_total[k] = round(plus_total.get(k), 1)
                    else:
                        plus_avg[k] = round(v, 3)
                        plus_total[k] = round(plus_total.get(k), 3)

                for k, v in minus_total.items():
                    if k in COUNTING_STATS:
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

            total_df, diff_df, avg_df, diff_avg_df = totals_and_avg(plus, minus)

            # --- Display in a single row (side-by-side layout) ---
            st.markdown("### 💼 Trade Comparison")
            
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
    else:
        st.write("Please return to Home Page and connect to your league.")




