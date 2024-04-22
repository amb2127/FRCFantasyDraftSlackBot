import app
import math
import random
import requests
import secret

from operator import itemgetter
from typing import List

game_list = dict()


class Player:
    def __init__(self, name: str, uid: str):
        self.name = name
        self.uid = uid
        self.picks = []


def delete(game_id: int):
    del game_list[game_id]


class Game:
    def __init__(self, teams: List[int], players: List[Player], max_players: int,
                 host_uid: str, channel_name: str, event_code: str, team_count: int = 4):
        self.teams = teams
        self.players = players
        self.max_players = max_players
        i = 0
        while i in game_list:
            i += 1
        self.game_id = i
        self.started = False
        self.host_uid = host_uid
        self.channel_name = channel_name
        self.up_next = []
        self.team_count = team_count
        self.completed = False
        self.picks = dict()
        self.event_code = event_code
        self.event_name = get_event_name(event_code)
        game_list.update({self.game_id: self})

    def get_available_teams(self) -> str:
        draft_pool = "```\nTeams: "
        for team in self.teams:
            draft_pool += f"{team}, "
        draft_pool += "\n```"
        return draft_pool

    def get_players(self) -> str:
        player_list = f"```\n{self.event_name} Draft: \n"

        for i in self.players:
            player_list += f"{i.name}" + " " * (12 - len(i.name))
            for j in range(self.team_count):
                if j < len(self.picks.get(i.uid)):
                    player_list += f"|{self.picks.get(i.uid)[j]}" + " " * (4 - len(str(self.picks.get(i.uid)[j])))
                else:
                    player_list += "|"
            player_list += "\n"

        player_list += "```"

        return player_list

    def get_player(self, uid: str):
        for player in self.players:
            if player.uid == uid:
                return player
        return None

    def add_player(self, player: Player):
        self.players.append(player)
        self.picks.update({player.uid: []})

    def start(self):
        if not self.completed or not self.started:
            self.started = True
            random.shuffle(self.players)
            for i in range(self.team_count):
                if i % 2 == 0:
                    temp = self.players.copy()
                else:
                    temp = self.players.copy()[::-1]
                for j in temp:
                    self.up_next.append(j)
            return True
        else:
            return False

    def get_up_next_msg(self):
        if len(self.up_next) == 1:
            return f"<@{self.up_next[0].uid}> is picking, nobody on deck"
        return f"<@{self.up_next[0].uid}> is picking, <@{self.up_next[1].uid}> on deck"

    def add_pick(self, team_num: int, player_uid: str) -> bool:
        picklist = self.picks.get(player_uid)
        if team_num in self.teams and len(picklist) < 4:
            picklist.append(team_num)
            self.teams.remove(team_num)
            return True
        else:
            return False

    def end(self):
        self.completed = True
        self.players.clear()

    def calculate_scores_and_print(self):
        if self.completed:
            scores = dict()
            for player in self.picks:
                score = 0
                for team in self.picks.get(player):
                    score += get_score(team, self.event_code)
                scores.update({player: score})

            scores = dict(sorted(scores.items(), key=itemgetter(1)))

            scores_list = "```\nScores: \n"
            for player in scores:
                scores_list += f"{app.get_username_from_id(player)}: {scores.get(player)}\n"
            scores_list += "```"
            return scores_list


def get_team_list_from_event(event_code: str) -> List[int]:
    url = "https://www.thebluealliance.com/api/v3/event/" + event_code + "/teams/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)

    data = r.json()

    teams = []

    for i in range(len(data)):
        teams.append(data[i]["team_number"])

    return sorted(teams)


def get_score(team_num: int, event_code: str) -> int:
    url = "https://www.thebluealliance.com/api/v3/team/frc" + str(team_num) + "/event/" + event_code + "/status"
    award_url = "https://www.thebluealliance.com/api/v3/team/frc" + str(team_num) + "/event/" + event_code + "/awards"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)
    data = r.json()

    sort_order_info = data["qual"]["sort_order_info"]

    rp_id = 0
    avg_auto_id = 0
    avg_match_id = 0

    for i in range(len(sort_order_info)):
        if sort_order_info[i]["name"] == "Ranking Points":
            rp_id = i
        elif sort_order_info[i]["name"] == "Avg Auto":
            avg_auto_id = i
        elif sort_order_info[i]["name"] == "Avg Match":
            avg_match_id = i

    ranking_pts = data["qual"]["ranking"]["sort_orders"][rp_id] * data["qual"]["ranking"]["matches_played"]
    auto_pts = data["qual"]["ranking"]["sort_orders"][avg_auto_id]
    match_pts = data["qual"]["ranking"]["sort_orders"][avg_match_id]

    qual_pts = ranking_pts * 0.8 + auto_pts * 0.3 + match_pts * 0.2

    playoff_pts = 0

    if data["playoff"] is not None:
        if data["playoff"]["playoff_type"] == 10:
            if data["playoff"]["double_elim_round"] == "Round 2":
                playoff_pts = 3
            elif data["playoff"]["double_elim_round"] == "Round 3":
                playoff_pts = 5
            elif data["playoff"]["double_elim_round"] == "Round 4":
                playoff_pts = 8
            elif data["playoff"]["double_elim_round"] == "Finals":
                playoff_pts = 10
            else:
                playoff_pts = 0
        else:
            playoff_pts = 0

    s = requests.get(url=award_url, params=params)
    awards = s.json()

    award_pts = 0

    if awards is None:
        award_pts = 0
    else:
        for award in awards:
            if "Winner" in award["name"]:
                award_pts += 5
            elif "Finalist" in award["name"]:
                award_pts += 1
            elif "Engineering Inspiration" in award["name"]:
                award_pts += 7
            elif "Chairman" in award["name"] or "FIRST Impact" in award["name"]:
                award_pts += 7
            else:
                award_pts += 2

    return math.ceil(qual_pts + playoff_pts + award_pts)


def get_event_name(event_code: str) -> str:
    url = "https://www.thebluealliance.com/api/v3/event/" + event_code + "/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)
    data = r.json()

    return str(data["year"]) + " " + data["name"]



