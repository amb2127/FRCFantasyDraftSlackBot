import requests
import secret

from typing import List

game_list = dict()


class Player:
    def __init__(self, name: str, uid: str):
        self.name = name
        self.uid = uid
        self.picks = []

    def add_pick(self, team_num: int, team_list: List[int]) -> bool:
        if team_num in team_list and len(self.picks) < 4:
            self.picks.append(team_num)
            team_list.remove(team_num)
            return True
        else:
            return False


def delete(game_id: int):
    del game_list[game_id]


class Game:
    def __init__(self, teams: List[int], players: List[Player], max_players: int, host_uid: str, channel_name: str):
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
        game_list.update({self.game_id: self})

    def get_available_teams(self) -> str:
        draft_pool = "```\nTeams: "
        for team in self.teams:
            draft_pool += f"{team}, "
        draft_pool += "\n```"
        return draft_pool

    def get_players(self) -> str:
        player_list = "```\nDraft: \n"

        for i in self.players:
            player_list += f"{i.name}" + " " * (12 - len(i.name))
            for j in range(4):
                if j < len(i.picks):
                    player_list += f"|{i.picks[j]}"
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

    def start(self):
        self.started = True


def get_team_list_from_event(event_code: str) -> List[int]:
    url = "https://www.thebluealliance.com/api/v3/event/" + event_code + "/teams/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)

    data = r.json()

    teams = []

    for i in range(len(data)):
        teams.append(data[i]["team_number"])

    return sorted(teams)
