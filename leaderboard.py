import math

import app
import pickle
import statistics


class LBEntry:
    def __init__(self, uid: str, elo: int):
        self.uid = uid
        self.elo = elo

    def __str__(self):
        return f"{app.get_username_from_id(self.uid)}: {self.elo}"

    def __lt__(self, other):
        return self.elo < other.elo


class LB:
    def __init__(self, lb: list[LBEntry]):
        self.lb = lb

    def get_player(self, uid: str) -> LBEntry:
        for i in self.lb:
            if i.uid == uid:
                return i

        print("creating player for ID", uid)
        new_player = LBEntry(uid, 1000)
        self.lb.append(new_player)
        return new_player


def freaky_regression(player_count: int):
    if player_count > 4:
        return 0.547*player_count + 4*math.sqrt(player_count) - 5.7663
    else:
        return player_count - 1


def update_scores(score_list): # this is gonna suck

    for player in score_list:


    leaderboard_msg = "```\nLeaderboard: \n"

    leaderboard_msg += "```"
    return leaderboard_msg


def get_leaderboard() -> LB:
    with open("leaderboard.txt", "rb") as f:
        lb = pickle.load(f)
    return lb


def leaderboard_to_string(lb: list[LBEntry]):
    lb_str = "```\nLeaderboard:\n"
    for i in lb:
        lb_str += str(i) + "\n"
    lb_str += "```"
    return lb_str


def add_leaderboard(lb: LB):
    lb.lb.sort()

    with open("leaderboard.txt", "wb") as f:
        pickle.dump(lb, f)
