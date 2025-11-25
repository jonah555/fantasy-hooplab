STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]

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

        data = player.stats or {}
        for stype in STATS_TYPES:
            self.stats[stype] = data.get(f"{player.year}_{stype}", {}).get("avg", {})


    def update_info(self, player_json):

        self.on_team_id = player_json.get("onTeamId", 0)
        self.status = player_json.get("status", "UNKNOWN")  # "FREEAGENT" or "WAIVERS"
        
        info = player_json.get("player", {})
        self.first_name = info.get("firstName")
        self.last_name =  info.get("lastName")

        ownership = info.get("ownership", {})
        self.avg_draft_pos = ownership.get("averageDraftPosition")
        self.percent_owned = ownership.get("percentOwned")
        