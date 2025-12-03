import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.player import RATING_CATS
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


def make_h2h_most_df(team_map, my_team_id):
    """Return DataFrame showing W-L-T and Win% for each team."""
    rows = []
    my_team = team_map.get(my_team_id)

    for t in team_map.values():
        h2h = t.h2h_most.get("total", {})
        result = h2h.get("result", "0-0-0")
        winpct = h2h.get("win%", 0)

        result = {
            "Team": t.name,
            "Record": result,
            "win%": round(winpct, 3)
        }
        if t.team_id != my_team.team_id:
            matchup = my_team.h2h_most.get("total", {}).get(t.team_id, {})
            result['you vs opp'] = matchup.get('score', '-')
            for cat in CATEGORIES:
                result[cat] = matchup[cat]

        rows.append(result)
        
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


# --- Helper: 
def get_position_color(position):
    """Returns line_color and fillcolor based on position"""
    colors = {
        'PG': {
            'line': '#EF5350',  # Red
            'fill': 'rgba(239, 83, 80, 0.3)'
        },
        'SG': {
            'line': '#FFA726',  # Orange
            'fill': 'rgba(255, 167, 38, 0.3)'
        },
        'SF': {
            'line': '#66BB6A',  # Green
            'fill': 'rgba(102, 187, 106, 0.3)'
        },
        'PF': {
            'line': '#1f77b4',  # Blue (the one you liked)
            'fill': 'rgba(31, 119, 180, 0.3)'
        },
        'C': {
            'line': '#AB47BC',  # Purple
            'fill': 'rgba(171, 71, 188, 0.3)'
        }
    }
    return colors.get(position, colors['PF'])  # Default to blue if position not found


# --- Helper: 
def create_radar(player_name, stats, position):
    # Define categories in clockwise order starting from 12 o'clock
    categories = RATING_CATS
    
    # Get values in the same order
    values = [stats.get(cat, 0) for cat in categories]
    
    # Close the loop by adding the first value at the end
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    # Get colors based on position
    colors = get_position_color(position)
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        line_color=colors['line'],
        fillcolor=colors['fill'],
        line_width=2
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickmode='array',
                tickvals=[1, 2, 3, 4, 5],
                showticklabels=False,
                gridcolor='#444444',  # Darker grid lines
                tickfont=dict(color='#CCCCCC')  # Light text for ticks
            ),
            angularaxis=dict(
                direction='clockwise',
                period=8,
                gridcolor='#444444',  # Darker grid lines
                tickfont=dict(color='#CCCCCC')  # Light text for labels
            ),
            bgcolor='#1E1E1E'  # Dark background for the polar area
        ),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=80, b=80),
        title=dict(text=f"{player_name} ({position})", x=0.5, xanchor='center', font=dict(color='#CCCCCC')),
        paper_bgcolor='#0E1117',  # Dark background for entire chart (matches Streamlit dark theme)
        plot_bgcolor='#0E1117'  # Dark background for plot area
    )
    
    return fig


def show_radar_charts(players, ratings):
    
    # Then add a search/filter for radar charts
    st.markdown("### 📊 View Player Radar Chart")

    # Dropdown to select player
    selected_player_name = st.selectbox(
        "Select a player to view their radar chart:",
        options=[p.name for p in players.values()],
        # key="player_select"
    )

    # Find the selected player
    selected_player = next((p for p in players.values() if p.name == selected_player_name), None)

    if selected_player:
        rating = selected_player.ratings['total']
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_radar(selected_player.name, rating, selected_player.position), width='stretch')
        
        with col2:
            st.subheader("Stats Breakdown")
            cola, colb, colc = st.columns(3)
            with cola:
                for cat in ["PTS", "REB", "AST"]:
                    st.metric(cat, ratings.get(rating.get(cat, 0)))
            with colb:
                for cat in ["3PM", "STL", "BLK"]:
                    st.metric(cat, ratings.get(rating.get(cat, 0)))
            with colc:
                for cat in ["FG%", "FT%"]:
                    st.metric(cat, ratings.get(rating.get(cat, 0)))


def show_players(player_map, team_map):
    st.markdown("### 🧍 Player Stats (total)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        player_view = st.radio("View:", ["Stats", "Z-Scores"], key="player_view", horizontal=True)
    with col2:
        
        ownderships = ['All', 'Free Agents']
        for t in team_map.values():
            ownderships.append(t.name)
        ownderships.append("Free Agents")
        ownership_filter = st.selectbox(
            "Ownership:",
            ownderships,
            index=ownderships.index('All'),  # no punting default
            key="ownership_filter"
        )
    with col3:
        punt_cats = st.multiselect(
            "Select categories to punt:",
            CATEGORIES,
            default=[],  # no punting default
            key="punt_select"
        )
    with col4:
        position_filter = st.multiselect(
            "Select Positions:",
            ['PG', 'SG', 'SF', 'PF', 'C'],
            default=['PG', 'SG', 'SF', 'PF', 'C'],  # no punting default
            key="pos_select"
        )


    rankings = fantasy.ranking_with_punting(player_map, CATEGORIES, punt_cats)

    player_rows = []

    for player in rankings['total']:
        p = player_map.get(player['player_id'])

        if p.position not in position_filter:
            continue  # Skip this player if position not selected
        if ownership_filter != 'All':
            if ownership_filter == 'Free Agents':
                if p.on_team_id != 0:
                    continue
            else:
                team = next((t for t in team_map.values() if t.name == ownership_filter), None)
                if not team or p.on_team_id != team.team_id:
                    continue
        
        ownership = (
            team_map[p.on_team_id].name if p.on_team_id in team_map
            else ("FA" if p.status == "FREEAGENT" else "WAIVER")
        )
        base = {
            "Rank" : player['rank'],
            "Name": p.name,
            "Ownership": ownership,
            "Pro Team": p.pro_team,
            "Pos": p.position,
            "Score": round(p.stats_z["total"].get("score", 0), 2),
            "Punted Score" : round(player['punted_value'], 2)
        }
        cats = CATEGORIES
        src = p.stats_z if player_view == "Z-Scores" else p.stats
        for cat in cats:
            val = src["total"].get(cat, 0)
            base[cat] = round_value(cat, val, player_view == "Z-Scores")
        base["ROS%"] = round(p.percent_owned, 1)
        player_rows.append(base)

    player_df = pd.DataFrame(player_rows)
    st.dataframe(player_df, width='stretch', height=len(player_df) * 35 + 38, hide_index=True)


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
    st.dataframe(team_df, width='stretch', hide_index=True)


def show_standings(team_map, my_team_id):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏆 League Standings H2H Most")
        df_most = make_h2h_most_df(team_map, my_team_id).sort_values("win%", ascending=False)
        st.dataframe(df_most, width='content', hide_index=True)
    with col2:
        st.markdown("### 🏆 League Standings H2H Each")
        df_each = make_h2h_each_df(team_map).sort_values("win%", ascending=False)
        st.dataframe(df_each, width='content', hide_index=True)


def show_roster(team_map, player_map, my_team_id, ratings):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧢 Team Roster Viewer")
    with col2:
        roster_view = st.radio("View:", ["Stats", "Z-Scores"], key="roster_view", horizontal=True)
    view = roster_view

    temp = {t.name: t for t in team_map.values()}
    team_names = list(temp.keys())
    selected_name = st.selectbox("Select team:", team_names, index=team_names.index(team_map.get(my_team_id).name))
    team = temp[selected_name]

    # Choose source
    is_z = view == "Z-Scores"
    stype = "total"

    roster_rows = []
    players = {}
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

        players[pid] = player

    roster_df = pd.DataFrame(roster_rows)
    st.dataframe(roster_df, width='stretch', height=len(roster_df) * 35 + 38)
    st.write("")
    show_radar_charts(players, ratings)


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


def show_trade(my_team_id, team_map, player_map, free_agents_map, counting_stats, percentage_stats, categories, cat_index, mask, roster_size):
    st.subheader("💼 Trade Analyzer")
    col1, col2, col3 = st.columns(3)
    # --- Team selectors ---

    team_names = [t.name for t in team_map.values()]
    with col1:
        team1_name = st.selectbox("Select Team 1", team_names, key="trade_team1", index=team_names.index(team_map.get(my_team_id).name))

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
        # bug: minus shouldn't have included Free Agents

        total_df, diff_df, avg_df, diff_avg_df = totals_and_avg(plus, minus, counting_stats)
        st.text("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### ⬆️ Players Gained ({team1_name})")
            st.dataframe(plus_df, width='content')
        with col2:
            st.markdown(f"#### ⬇️ Players Lost ({team1_name})")
            st.dataframe(minus_df, width='content')
        st.text("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Trade Summary (Totals)")
            st.dataframe(total_df, width='content')
            st.dataframe(diff_df, width='content')
        with col2:
            st.markdown("### 📊 Trade Summary (Averages)")
            st.dataframe(avg_df, width='content')
            st.dataframe(diff_avg_df, width='content')

        st.text("")
        show_standings(team_map, team1.team_id)
        st.text("")
        show_teams(team_map, counting_stats, roster_size, '_t')


def show_matchup(team_map, player_map, free_agents_map, my_team_id, league, counting_stats, percentage_stats):
    
    matchup_map = fantasy.build_matchup_scoring_period(league)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Select Matchup Teams")
    with col2:
        current_matchup_period = st.selectbox(
            "Select Week:",
            options=list(matchup_map.keys()),
            index=list(matchup_map.keys()).index(str(league.currentMatchupPeriod)),
            key="matchup_week_select"
        )

    current_matchup_period = int(current_matchup_period)
    team_names = {t.team_id: t.name for t in team_map.values()}
    colA, colB = st.columns(2)

    with colA:
        team1_id = st.selectbox(
            "Team 1 (Your Team)",
            options=list(team_names.keys()),
            index=list(team_names.keys()).index(my_team_id),
            format_func=lambda tid: team_names[tid],
            key="matchup_team1_select"
        )

    # Get matchup opponent by ESPN schedule
    matchup = team_map[team1_id].schedule[current_matchup_period - 1]
    opponent_id = matchup.away_team.team_id if matchup.home_team.team_id == team1_id else matchup.home_team.team_id

    with colB:
        options = list(n for n in team_names.keys() if n != team1_id)
        team2_id = st.selectbox(
            "Team 2 (Opponent)",
            options=options,
            index=options.index(opponent_id),
            format_func=lambda tid: team_names[tid],
            key="matchup_team2_select"
        )

    team_box_score = {}
    opponent_box_score = {}
    if current_matchup_period <= league.currentMatchupPeriod:
        team_box_score = fantasy.get_box_score(team1_id, current_matchup_period, team_map)
        opponent_box_score = fantasy.get_box_score(team2_id, current_matchup_period, team_map)

        col1, col2 = st.columns(2)
        with col1:
            df = pd.DataFrame(team_box_score, index=['team'])
            st.dataframe(df, width=900)
        with col2:
            df = pd.DataFrame(opponent_box_score, index = ['opp'])
            st.dataframe(df, width=900)

    team_games, opponent_games, free_agents_games = fantasy.get_matchup(team1_id, team2_id, current_matchup_period, league, 
                                                                        team_map, matchup_map, player_map, free_agents_map)

    scoring_period = matchup_map[str(current_matchup_period)]

    DAY_LABELS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    day_map = dict(zip(scoring_period, DAY_LABELS))

    def render_checkbox_grid(title, games_dict):
        st.markdown(f"### {title}")

        rows = []
        player_ids = list(games_dict.keys())

        # Build empty collection container
        selected = {pid: [] for pid in player_ids}

        # Header
        header_cols = st.columns(len(scoring_period) + 1)
        header_cols[0].markdown("**Player**")
        for i, day in enumerate(scoring_period):
            header_cols[i + 1].markdown(f"**{day_map[day]}**")

        # Rows
        for pid in player_ids:
            player = player_map.get(pid)
            row = st.columns(len(scoring_period) + 1)
            row[0].write(player.name)

            for i, day in enumerate(scoring_period):
                if day in games_dict[pid]:
                    team = games_dict[pid][day]["team"]
                    key = f"{title}_{pid}_{day}"
                    checked = row[i + 1].checkbox(team, key=key)
                    if checked:
                        selected[pid].append(day)
                else:
                    row[i + 1].write("-")

        return selected

    col1, col2 = st.columns(2)

    with col1:
        team1_selected = render_checkbox_grid(team_names[team1_id], team_games)
        # fa_selected_left = render_checkbox_grid("Free Agents (Left)", fa_games_raw)

    with col2:
        team2_selected = render_checkbox_grid(team_names[team2_id], opponent_games)
        # fa_selected_right = render_checkbox_grid("Free Agents (Right)", fa_games_raw)


    # Merge FA selections into both teams
    # team1_selected.update(fa_selected_left)
    # team2_selected.update(fa_selected_right)


    # -------------------------------
    # Run Button
    # -------------------------------
    run_btn = st.button("Run Projections", type="primary")

    if run_btn:
        st.subheader("📊 Matchup Projection Results")

        result, team_projections, opponent_projections = fantasy.analyze_matchup(team1_selected, team2_selected, team_box_score, opponent_box_score, 
                                                                        CATEGORIES, counting_stats, percentage_stats, player_map)


        df = pd.DataFrame(team_projections["total"], index=["team"])
        st.dataframe(df, width=900)

        df = pd.DataFrame(opponent_projections["total"], index=["opp"])
        st.dataframe(df, width=900)


        df = pd.DataFrame(result["total"], index=["Projected Diff"])
        st.dataframe(df, width=900)