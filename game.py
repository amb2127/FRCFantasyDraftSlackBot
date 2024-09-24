import app
import leaderboard
import math
import random
import requests
import secret

from operator import itemgetter
from pyerf import erfinv
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
    def __init__(self, teams: List[int], players: List[Player],
                 host_uid: str, channel_name: str, event_code: str, team_count: int = 4):
        self.teams = teams
        self.players = players
        self.max_players = math.floor(len(teams) / team_count)
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
        if team_num in self.teams and len(picklist) < self.team_count:
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

            lb_msg = leaderboard.update_scores(scores)

            scores_list = "```\nScores: \n"
            for player in scores:
                scores_list += f"{app.get_username_from_id(player)}: {scores.get(player)}\n"
            scores_list += "```"
            return scores_list, lb_msg


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

    qual = data["qual"]
    _r = int(qual["ranking"]["rank"])
    _n = int(qual["num_teams"])
    _alpha = 1.07

    qual_points = math.ceil(erfinv((_n - 2 * _r + 2) / (_alpha * _n)) * (10 / erfinv(1 / _alpha)) + 12)

    alliance = data["alliance"]
    alliance_points = 0

    if alliance is not None:
        if alliance["pick"] == 3:
            alliance_points = 0
        elif alliance["pick"] == 2:
            alliance_points = alliance["number"]
        else:
            alliance_points = 17 - alliance["number"]

    playoff = data["playoff"]
    playoff_points = 0

    if playoff is not None:
        if playoff["playoff_type"] == 10:
            if playoff["double_elim_round"] == "Round 4":
                playoff_points = 7
            elif playoff["double_elim_round"] == "Round 5":
                playoff_points = 10
            elif playoff["double_elim_round"] == "Finals":
                playoff_points = 20

            if playoff["status"] == "won":
                playoff_points += 10
        else:
            playoff_points = playoff["record"]["wins"] * 5

    award_r = requests.get(url=award_url, params=params)
    award_data = award_r.json()

    award_points = 0

    for i in award_data:
        if "Finalist" in i["name"] or "Winners" in i["name"] or "Winner" in i["name"]:
            award_points += 0
        elif "Chairman's" in i["name"] or "Impact" in i["name"]:
            award_points += 10
        elif "Rookie All Star" in i["name"] or "Engineering Inspiration" in i["name"]:
            award_points += 8
        else:
            award_points += 5

    print("Team", team_num, "\nQual:", qual_points, "\nAlliance:", alliance_points,
          "\nPlayoff:", playoff_points, "\nAward:", award_points)

    raw_score = qual_points + alliance_points + playoff_points + award_points

    if team_num == 5199:
        raw_score -= 10

    return raw_score


def get_event_name(event_code: str) -> str:
    url = "https://www.thebluealliance.com/api/v3/event/" + event_code + "/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)
    data = r.json()

    return str(data["year"]) + " " + data["name"]
