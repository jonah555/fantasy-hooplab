from utils.player import Player
from utils.team import Team
import numpy as np
import json
# from datetime import datetime, timedelta


STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]


def get_roster(league, roster_size, team_count):
    """Returns:
    team_map = {team_id: Team()}
    player_map = {player_id: Player()}
    """
    team_map = {}
    player_map = {}
    free_agents_map = {}
    top_players_map = {}

    # Rostered
    for team in league.teams:
        team_obj = Team(team)
        team_map[team.team_id] = team_obj

        for player in team.roster:
            player_obj = Player(player)
            player_map[player_obj.player_id] = player_obj

    # FA
    for player in league.free_agents(size=500):
        player_obj = Player(player)
        player_map[player_obj.player_id] = player_obj
        free_agents_map[player_obj.player_id] = player_obj

    # add additional info
    filters = {
        "players": {
            "limit": 500,
            "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
        }
    }
    params = {"view": "kona_player_info"}
    headers = {"x-fantasy-filter": json.dumps(filters)}
    data = league.espn_request.league_get(params=params, headers=headers)
    
    rostered_size = team_count * roster_size

    for rank, player_json in enumerate(data["players"]):

        player_id = player_json.get('id')

        if player_map.get(player_id):
            player_map.get(player_id).update_info(player_json, league.pro_schedule)

        if rank < rostered_size:
            top_players_map[player_id] = player_map.get(player_id)
    
    return team_map, player_map, free_agents_map, top_players_map


def get_mean_std(obj_map, categories, cat_index):
    # helper
    """Compute mean and std using NumPy (fast and stable)."""
    mean_dict = {stype: {} for stype in STATS_TYPES}
    std_dict = {stype: {} for stype in STATS_TYPES}

    for stype in STATS_TYPES:
        values = np.array([
            [obj.stats[stype].get(cat, 0) for cat in categories]
            for obj in obj_map.values()
        ], dtype=float)

        means = np.mean(values, axis=0)
        stds = np.std(values, axis=0)
        stds = np.where(stds == 0, 1, stds)

        for idx in cat_index:
            cat = categories[idx]
            mean_dict[stype][cat] = means[idx]
            std_dict[stype][cat] = stds[idx]

    return mean_dict, std_dict


def add_z_scores(obj, mean, std, categories, cat_index, mask):
    # helper
    """Assign z-scores per object using vectorized NumPy."""
    for stype in STATS_TYPES:
        # setdefault() inserts {} into dict if stype missing
        # get() returns {} but does NOT store it in the dict
        #       -> you’d just be modifying a temporary dict that disappears right after unless the key already existed
        stats_z = obj.stats_z.setdefault(stype, {}) 
        stats_z.clear()

        values = np.array([obj.stats[stype].get(cat, 0) for cat in categories], dtype=float)
        means = np.array([mean[stype][cat] for cat in categories], dtype=float)
        stds = np.array([std[stype][cat] for cat in categories], dtype=float)

        z_scores = (values - means) / stds
        z_scores[mask] = -z_scores[mask]

        for idx in cat_index:
            stats_z[categories[idx]] = z_scores[idx]

        stats_z["score"] = float(np.sum(z_scores))


def compute_players_z_scores(player_map, top_players_map, categories, cat_index, mask):
    """Master function for stats aggregation and z-score computation."""
    
    # Mean and std separately for top players for later z score calculations
    players_mean, players_std = get_mean_std(top_players_map, categories, cat_index)

    # Apply z-scores to players
    for player in player_map.values():
        add_z_scores(player, players_mean, players_std, categories, cat_index, mask)


def compute_teams_z_scores(team_map, player_map, categories, cat_index, mask, 
                           counting_stats, percentage_stats, roster_size):
    """Master function for stats aggregation and z-score computation."""
    # 1. Compute team stats first (needed before normalization)
    for team in team_map.values():
        team.compute_team_stats(player_map, counting_stats, percentage_stats, roster_size)

    # 2. Mean and std separately for teams and players
    teams_mean, teams_std = get_mean_std(team_map, categories, cat_index)
    
    # 3. Apply z-scores to teams
    for team in team_map.values():
        add_z_scores(team, teams_mean, teams_std, categories, cat_index, mask)

    # 4. Compute records (h2h)
    for team in team_map.values():
        team.get_record(team_map, categories)


def update_roster(actions, team_map, player_map):
    """
    Make a new copy of team_map and update rosters based on actions.
    actions = {player_id: dest} where dest = team_id or -1 for free agent
    """
    # reset rosters back to original rosters in real life
    for team in team_map.values():
        team.reset_roster() 

    for player_id, dest in actions.items():
        player = player_map.get(player_id)
        if not player:
            continue  # skip missing player

        prev = player.on_team_id
        if prev in team_map and player_id in team_map[prev].roster:
            team_map[prev].roster.remove(player_id)
            # player["on_team_id"] = dest

        if dest in team_map:
            team_map[dest].roster.append(player_id)
        # else:
            # player["on_team_id"] = 0
            # player["status"] = "WAIVERS"


def compute_transaction(players, player_map, counting_stats, percentage_stats):
    # helper
    info = {stype : {'total': {cat : 0 for cat in counting_stats} } for stype in STATS_TYPES}
    info['size'] = len(players)
    for player_id in players:
        player = player_map.get(player_id)
        for stype in STATS_TYPES:
            info.get(stype)[player_id] = player.stats.get(stype)
            for cat in counting_stats:
                info.get(stype)['total'][cat] += player.stats.get(stype).get(cat, 0)

    for stype in STATS_TYPES:
        for stats in percentage_stats:
            made = info.get(stype).get('total').get(f"{stats}M")
            attempt = info.get(stype).get('total').get(f"{stats}A")
            info[stype]['total'][f"{stats}%"] = made / attempt if attempt else 0

    return info


def analyze_transaction(result, actions, player_map, team_map, counting_stats, percentage_stats,
                        categories, cat_index, mask, roster_size):

    plus = compute_transaction(result.get('plus'), player_map, counting_stats, percentage_stats)
    minus = compute_transaction(result.get('minus'), player_map, counting_stats, percentage_stats)


    # needs show oroginal stats, z_scores and standings before updating
    update_roster(actions, team_map, player_map)
    compute_teams_z_scores(team_map, player_map, categories, cat_index, mask, counting_stats, percentage_stats, roster_size)

    return plus, minus


def reset_roster(team_map, player_map, categories, cat_index, mask, counting_stats, percentage_stats, roster_size):
    for team in team_map.values():
        team.reset_roster() 
    compute_teams_z_scores(team_map, player_map, categories, cat_index, mask, counting_stats, percentage_stats, roster_size)    


def build_matchup_scoring_period(league, all_star_week=17):

    matchup_periods = league.settings.matchup_periods

    matchup_map = {week : [] for week in matchup_periods}

    for day in range(league.firstScoringPeriod, league.finalScoringPeriod + 1):
        week = (day // 7) + 1
        week -= 1 if week > all_star_week else 0
        matchup_map.get(f'{week}').append(day)
    
    return matchup_map 


def get_box_score(team_id, current_matchup_period, team_map, all_categories):

    my_team = team_map.get(team_id)
    matchup = my_team.schedule[current_matchup_period - 1] # my_team.schedule starts index 0
    
    box_score = {cat : 0 for cat in all_categories}

    home = team_id == matchup.home_team.team_id
    
    for cat in all_categories:
        if home:
            box_score[cat] = matchup.home_team_cats.get(cat, {}).get('score', 0)
        else:
            box_score[cat] = matchup.away_team_cats.get(cat, {}).get('score', 0)

    return box_score


def count_games(players, player_map, scoring_period, today):
    # helper
    games = {player_id : {} for player_id in players}
    for player_id in players:
        player = player_map.get(player_id)
        for day in scoring_period:
            if day >= today and f'{day}' in player.schedule: # and player.schedule.get(f'{day}').get('date') >= datetime.now() - timedelta(hours=2, minutes=30):
                games[player_id][day] = player.schedule.get(f'{day}')

    return games


def sum_projections(games, box_score, counting_stats, percentage_stats, player_map):
    # helper
    projections = {stype : box_score.copy() for stype in STATS_TYPES}

    for player_id, days in games.items():
        for day in days:
            player = player_map[player_id]
            for stype in STATS_TYPES:
                for cat in counting_stats:
                    projections[stype][cat] += player.stats[stype].get(cat, 0)
    
    for stype in STATS_TYPES:
        for stats in percentage_stats:
            made = projections.get(stype).get(f'{stats}M')
            attempt = projections.get(stype).get(f'{stats}A')
            projections[stype][f'{stats}%'] = made / attempt if attempt else 0.0


    return projections


def analyze_matchup(team_games, opponent_games, team_box_score, opponent_box_score, all_categories, counting_stats, percentage_stats, player_map):

    team_projections = sum_projections(team_games, team_box_score, counting_stats, percentage_stats, player_map)
    opponent_projections = sum_projections(opponent_games, opponent_box_score, counting_stats, percentage_stats, player_map)

    result = {stype: {cat: 0 for cat in all_categories} for stype in STATS_TYPES}

    for stype in STATS_TYPES:
        for cat in all_categories:
            result[stype][cat] = team_projections[stype][cat] - opponent_projections[stype][cat]
            if cat in counting_stats:
                result[stype][cat] = round(result[stype][cat], 0)
                team_projections[stype][cat] = round(team_projections[stype][cat], 0)
                opponent_projections[stype][cat] = round(opponent_projections[stype][cat], 0)
            else:
                result[stype][cat] = round(result[stype][cat], 4)
                team_projections[stype][cat] = round(team_projections[stype][cat], 4)
                opponent_projections[stype][cat] = round(opponent_projections[stype][cat], 4)

    return result, team_projections, opponent_projections


def ranking_with_punting(player_map, categories, punting_cats):
    result = {}
    
    for stype in STATS_TYPES:
        players_data = []
        
        for player_id, player in player_map.items():
            # Get z-scores for this stat type
            z_scores = player.stats_z.get(stype, {})
            
            # Calculate punted value (sum of z-scores excluding punting_cats)
            punted_value = sum(
                z_scores.get(cat, 0) 
                for cat in categories 
                if cat not in punting_cats
            )
            
            players_data.append({
                'rank' : 0,
                'player_id': player_id,
                'name': player.name,
                'punted_value': punted_value,
                # 'stats_z': z_scores.copy()  # Include all z-scores
            })
        
        # Sort by punted_value descending (highest first)
        players_data.sort(key=lambda x: x['punted_value'], reverse=True)
        
        # Add ranking
        for rank, player_data in enumerate(players_data, start=1):
            player_data['rank'] = rank
        
        result[stype] = players_data
    
    return result