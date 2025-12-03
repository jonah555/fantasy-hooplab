import streamlit as st
import numpy as np
import pandas as pd
import espn_api.basketball as api
from utils import fantasy, render

YEAR = 2026
ROSTER_SIZE = 13
TEAM_COUNT = 10
CATEGORIES = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
CAT_INDEX = np.arange(len(CATEGORIES))
COUNTING_STATS = ["PTS", "3PM", "REB", "AST", "STL", "BLK", "TO", "FGM", "FGA", "FTM", "FTA"]
PERCENTAGE_STATS = ["FG", "FT"]
NEGATIVE_STATS = ["TO"]
MASK = np.array([cat in NEGATIVE_STATS for cat in CATEGORIES])
STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]
RATINGS = {5: 'S', 4: 'A', 3: 'B', 2: 'C', 1: 'D'}


st.set_page_config(page_title="Fantasy HoopLab", layout="wide")
st.title("🏀 Fantasy HoopLab")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Home", "Players", "Teams" ,"Standings", "Roster", "Chart", "Trade", "Matchup"])

if "league" not in st.session_state:
    st.session_state.league = None

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
        for key in st.session_state.keys():
            del st.session_state[key]
        try:
            league, team_map, player_map, free_agents_map, top_players_map = load_league_data(
                league_id, YEAR, ROSTER_SIZE, TEAM_COUNT
            )
            st.session_state.league = league
            st.session_state.team_map = team_map
            st.session_state.player_map = player_map
            st.session_state.free_agents_map = free_agents_map
            st.session_state.top_players_map = top_players_map
            st.session_state.last_updated = pd.Timestamp.now()
            st.session_state.my_team_id = None
        except:
            st.write("Connection failed.")
            st.session_state.league = None
            
        
    if st.session_state.league:
        st.write("Successfully connected to ESPN Fantasy League!")
        fantasy.compute_players_z_scores(st.session_state.player_map, st.session_state.top_players_map, CATEGORIES, CAT_INDEX, MASK)
        fantasy.compute_teams_z_scores(st.session_state.team_map, st.session_state.player_map, CATEGORIES, CAT_INDEX, MASK, 
                                       COUNTING_STATS, PERCENTAGE_STATS, ROSTER_SIZE)
        st.caption(f"Last updated: {st.session_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write('')

        team_names = {t.team_id: t.name for t in st.session_state.team_map.values()}
        my_team_id = st.selectbox("Select Your Team", options=list(team_names.keys()), format_func=lambda tid: team_names[tid])
        my_team_id_btn = st.button("Save")
        if my_team_id_btn:
            st.session_state.my_team_id = my_team_id
    else:
        st.write("Please make sure your league is set to public and league ID is correct.")

        

# 2. Players
with tab2:
    st.header("Players")
    if st.session_state.league:
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map
        render.show_players(player_map, team_map)
    else:
        st.write("Please return to Home Page and connect to your league.")
        

# 3. Teams
with tab3:
    st.header("Teams")
    if st.session_state.league:
        team_map = st.session_state.team_map
        fantasy.reset_roster(team_map, player_map, CATEGORIES, CAT_INDEX, MASK, COUNTING_STATS, PERCENTAGE_STATS, ROSTER_SIZE)
        render.show_teams(team_map, COUNTING_STATS, ROSTER_SIZE, '')
    else:
        st.write("Please return to Home Page and connect to your league.")


# 4. Standings
with tab4:
    st.header("Standings")
    if st.session_state.league:
        if st.session_state.my_team_id:
            team_map = st.session_state.team_map
            my_team_id = st.session_state.my_team_id
            render.show_standings(team_map, my_team_id)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")


# 5. Roster
with tab5:
    st.header("Roster")
    if st.session_state.league:
        if st.session_state.my_team_id:
            team_map = st.session_state.team_map
            player_map = st.session_state.player_map
            my_team_id = st.session_state.my_team_id
            render.show_roster(team_map, player_map, my_team_id, RATINGS)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")


# 6. Chart
with tab6:
    st.header("Chart")
    if st.session_state.league:
        player_map = st.session_state.player_map
        rankings = fantasy.ranking_with_punting(player_map, CATEGORIES, [])
        stype = st.selectbox("Select Stats Type", options=STATS_TYPES, index=STATS_TYPES.index("total"))
        players = {p['player_id'] : player_map.get(p['player_id']) for p in rankings[stype]}
        render.show_radar_charts(players, RATINGS)
    else:
        st.write("Please return to Home Page and connect to your league.")


# 7. Trade
with tab7:
    st.header("Trade")
    if st.session_state.league:
        if st.session_state.my_team_id:
            team_map = st.session_state.team_map
            player_map = st.session_state.player_map
            free_agents_map = st.session_state.free_agents_map
            my_team_id = st.session_state.my_team_id
            render.show_trade(my_team_id, team_map, player_map, free_agents_map, COUNTING_STATS, PERCENTAGE_STATS, 
                              CATEGORIES, CAT_INDEX, MASK, ROSTER_SIZE)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")



# 8. Matchup
with tab8:
    st.header("Matchup")
    if st.session_state.league:
        if st.session_state.my_team_id:
            league = st.session_state.league
            team_map = st.session_state.team_map
            player_map = st.session_state.player_map
            free_agents_map = st.session_state.free_agents_map
            my_team_id = st.session_state.my_team_id
            render.show_matchup(team_map, player_map, free_agents_map, my_team_id, league, COUNTING_STATS, PERCENTAGE_STATS)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")

