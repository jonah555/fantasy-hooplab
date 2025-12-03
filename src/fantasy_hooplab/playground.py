import streamlit as st
import numpy as np
import pandas as pd
import espn_api.basketball as api
from utils import fantasy, render
import plotly.graph_objects as go # not in requirements.txt
from datetime import datetime


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




