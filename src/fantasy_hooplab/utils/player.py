STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]
RATING_CATS = ["PTS", "3PM", "AST", "STL", "FT%", 'FG%', 'BLK', "REB"]
CRITERIAS = {
    "PTS" : [23, 18, 14, 10], 
    "3PM" : [2.8, 2, 1.3, 0.4], 
    "AST" : [6.2, 4.3, 3, 1.8], 
    "STL" : [1.5, 1.2, 0.9, 0.7], 
    "FT%" : [.87, .83, .78, .75], 
    'FG%' : [.54, .5, .46, .43], 
    'BLK' : [1.3, 0.8, 0.5, 0.3], 
    "REB" : [8.5, 6, 4.8, 3.5]
}

class Player:
    def __init__(self, player):

        self.player_id = player.playerId
        self.name = player.name
        self.pro_team = player.proTeam
        self.position = player.position
        self.eligible_slots = player.eligibleSlots
        self.schedule = player.schedule
        self.pos_rank = player.posRank

        # self.lineup_slot = player.lineupSlot     # we save IR in Team()
        self.injury_status = player.injuryStatus
        self.expected_return_date = player.expected_return_date
        self.news = player.news
        
        self.on_team_id = 0
        self.status = ""
        self.first_name = ""
        self.last_name =  ""
        self.avg_draft_pos = 0
        self.percent_owned = 0

        self.stats = {}
        self.stats_z = {}
        
        self.ratings = {}

        data = player.stats or {}
        for stype in STATS_TYPES:
            self.stats[stype] = data.get(f"{player.year}_{stype}", {}).get("avg", {})
            self.ratings[stype] = {cat : 0 for cat in RATING_CATS}

            for cat in RATING_CATS:
                stat = self.stats[stype].get(cat, 0)
                self.ratings[stype][cat] = self.rate_category(stat, cat)

    
    def rate_category(self, stat, category):
        index = 0
        criteria = CRITERIAS.get(category)
        while index < len(criteria):
            if (stat >= criteria[index]):
                break
            index += 1
        return 5 - index


    def update_info(self, player_json):

        self.on_team_id = player_json.get("onTeamId", 0)
        self.status = player_json.get("status", "UNKNOWN")  # "FREEAGENT" or "WAIVERS"
        
        info = player_json.get("player", {})
        self.first_name = info.get("firstName")
        self.last_name =  info.get("lastName")

        ownership = info.get("ownership", {})
        self.avg_draft_pos = ownership.get("averageDraftPosition")
        self.percent_owned = ownership.get("percentOwned")
        