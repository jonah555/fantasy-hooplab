import numpy as np

STATS_TYPES = ["projected", "total", "last_30", "last_15", "last_7"]
CATEGORIES = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
CAT_INDEX = np.arange(len(CATEGORIES))

class Team():
    def __init__(self, team):
        self.team_id = team.team_id
        self.team_abbrev = team.team_abbrev
        self.name = team.team_name
        self.schedule = team.schedule
        self.logo_url = team.logo_url

        self.roster = [player.playerId for player in team.roster]
        self.original_roster = self.roster.copy()  # save original
        self.injury_reserved = [player.playerId for player in team.roster if player.lineupSlot == "IR"]

        self.stats = {}
        self.stats_z = {}
        self.h2h_most = {}
        self.h2h_each = {} 


    def reset_roster(self):
        self.roster.clear()
        self.roster = self.original_roster.copy()


    def compute_team_stats(self, player_map, counting_stats, percentage_stats, roster_size):
        """
        Compute aggregate raw stats for the team.
        """
        self.stats.clear()
        self.stats = {stype: {cat: 0 for cat in ["MIN"] + counting_stats} for stype in STATS_TYPES}

        for player_id in self.roster:

            if player_id in self.injury_reserved and len(self.roster) > roster_size:
                continue    # skip IR

            player = player_map.get(player_id)

            for stype in STATS_TYPES:
                stats = player.stats.get(stype, {})
                self.stats[stype]["MIN"] += stats.get("MIN", 0)
                for cat in counting_stats:
                    self.stats[stype][cat] += stats.get(cat, 0)

        for stype in STATS_TYPES:
            for cat in percentage_stats:
                made = self.stats[stype].get(f"{cat}M", 0)
                attempted = self.stats[stype].get(f"{cat}A", 0)
                # Safely compute FG% & FT% (0 == False else True) 
                self.stats[stype][f"{cat}%"] = (made / attempted) if attempted else 0


    def h2h(self, opp, opp_id, categories, total_most, total_each):
        """
        Compute head-to-head stats versus one opponent.
        Uses overwriting into preallocated dicts.
        """
        for stype in STATS_TYPES:
            # Vector of differences for all categories
            diffs = np.array([
                self.stats_z[stype][cat] - opp.stats_z[stype][cat]
                for cat in categories
            ])

            # Preallocated matchup entry
            matchup = self.h2h_most[stype][opp_id]

            # Result win-loss (aggregate)
            win = np.count_nonzero(diffs > 0)
            loss = np.count_nonzero(diffs < 0)
            matchup["result"] = int(win - loss)

            # Per-category W/L/T updates
            for index in CAT_INDEX:
                cat = categories[index]
                matchup[cat] = diffs[index]  # overwrite value, no new key

                if diffs[index] > 0:
                    self.h2h_each[stype][cat][0] += 1; total_each[stype][0] += 1
                elif diffs[index] < 0:
                    self.h2h_each[stype][cat][1] += 1; total_each[stype][1] += 1
                else:
                    self.h2h_each[stype][cat][2] += 1; total_each[stype][2] += 1

            # Update total W-L-T for h2h_most
            if matchup["result"] > 0:
                total_most[stype][0] += 1
            elif matchup["result"] < 0:
                total_most[stype][1] += 1
            else:
                total_most[stype][2] += 1


    def get_record(self, team_map, categories):
        """
        Compute head-to-head and per-category records.
        No dict growth during loop (preallocated).
        """
        
        num_opponents = max(1, len(team_map) - 1)
        num_categories = len(categories)

        # ---- Preallocate h2h_most ----
        self.h2h_most.clear()
        self.h2h_most = {
            stype: {
                opp_id: {"result": 0}  # ready to overwrite diffs in h2h()
                for opp_id in team_map if opp_id != self.team_id
            }
            for stype in STATS_TYPES
        }

        # ---- Preallocate h2h_each ----
        self.h2h_each.clear()
        self.h2h_each = {
            stype: {cat: [0, 0, 0] for cat in categories} 
            for stype in STATS_TYPES
        }

        total_most = {stype: [0, 0, 0] for stype in STATS_TYPES}
        total_each = {stype: [0, 0, 0] for stype in STATS_TYPES}

        # ---- Evaluate each opponent ----
        for opp_id, opp in team_map.items():
            if opp_id != self.team_id:
                self.h2h(opp, opp_id, categories, total_most, total_each)

        # ---- Final W-L-T & win% summaries ----
        for stype in STATS_TYPES:
            w, l, t = total_most[stype]
            self.h2h_most[stype]["result"] = f"{w}-{l}-{t}"
            self.h2h_most[stype]["win%"] = (w + 0.5 * t) / num_opponents

            w, l, t = total_each[stype]
            self.h2h_each[stype]["result"] = f"{w}-{l}-{t}"
            self.h2h_each[stype]["win%"] = (w + 0.5 * t) / (num_opponents * num_categories)

        return self.h2h_most, self.h2h_each
