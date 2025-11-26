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


st.set_page_config(page_title="Fantasy HoopLab", layout="wide")
st.title("🏀 Fantasy HoopLab")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Players", "Teams" ,"Standings", "Roster", "Trade"])

if "league" not in st.session_state:
    st.session_state.league = None
    st.session_state.team_map = None
    st.session_state.player_map = None
    st.session_state.free_agents_map = None
    st.session_state.top_players_map = None
    st.session_state.last_updated = None
    st.session_state.my_team = None


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
        st.session_state.last_updated = pd.Timestamp.now()
        
    if st.session_state.league:
        st.write("Successfully connected to ESPN Fantasy League!")
        fantasy.compute_players_z_scores(st.session_state.player_map, st.session_state.top_players_map, CATEGORIES, CAT_INDEX, MASK)
        fantasy.compute_teams_z_scores(st.session_state.team_map, st.session_state.player_map, CATEGORIES, CAT_INDEX, MASK, 
                                       COUNTING_STATS, PERCENTAGE_STATS, ROSTER_SIZE)
        st.caption(f"Last updated: {st.session_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write('')
        team_names = [t.name for t in st.session_state.team_map.values()]
        my_team = st.selectbox("Select Your Team", team_names, key="user_team")
        my_team_btn = st.button("Save")
        if my_team_btn:
            st.session_state.my_team = my_team
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
        if st.session_state.my_team:
            team_map = st.session_state.team_map
            my_team = st.session_state.my_team
            render.show_standings(team_map, my_team)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")


# 5. Roster
with tab5:
    st.header("Roster")
    if st.session_state.league:
        team_map = st.session_state.team_map
        player_map = st.session_state.player_map

        render.show_roster(team_map, player_map)
    else:
        st.write("Please return to Home Page and connect to your league.")


# 6. Trade
with tab6:
    st.header("Trade")
    if st.session_state.league:
        if st.session_state.my_team:
            team_map = st.session_state.team_map
            player_map = st.session_state.player_map
            free_agents_map = st.session_state.free_agents_map
            my_team = st.session_state.my_team

            render.show_trade(my_team, team_map, player_map, free_agents_map, COUNTING_STATS, PERCENTAGE_STATS, 
                              CATEGORIES, CAT_INDEX, MASK, ROSTER_SIZE)
        else:
            st.write("Please return to Home Page and select your team.")
    else:
        st.write("Please return to Home Page and connect to your league.")




