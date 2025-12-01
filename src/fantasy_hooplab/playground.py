import streamlit as st
import numpy as np
import pandas as pd
import espn_api.basketball as api
from utils import fantasy, render
import plotly.graph_objects as go # not in requirements.txt


LEAGUE_ID = 816907987
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


league = api.League(league_id=LEAGUE_ID, year=YEAR)
team_map, player_map, free_agents_map, top_players_map = fantasy.get_roster(league, ROSTER_SIZE, ROSTER_SIZE)

fantasy.compute_players_z_scores(player_map, top_players_map, CATEGORIES, CAT_INDEX, MASK)
fantasy.compute_teams_z_scores(team_map, player_map, CATEGORIES, CAT_INDEX, MASK, COUNTING_STATS, PERCENTAGE_STATS, ROSTER_SIZE)


player_name = "Stephen Curry"
player = player_map.get(league.player_map.get(player_name))
rating = player.ratings['total']
position = player.position

# Define categories in clockwise order starting from 12 o'clock
categories = ["PTS", "FT%", "AST", "STL", "3PM", 'BLK', "REB", 'FG%']

# Get values in the same order
values = [rating.get(cat, 0) for cat in categories]

# Close the loop by adding the first value at the end
values_closed = values + [values[0]]
categories_closed = categories + [categories[0]]

# Get colors based on position
colors = render.get_position_color(position)

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

st.plotly_chart(fig, width='stretch')