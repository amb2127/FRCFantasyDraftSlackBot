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


def update_scores(score_list):
    score_data = []

    for player in score_list:
        score_data.append(score_list.get(player))

    score_data.sort()

    mean_score = statistics.mean(score_data)
    if len(score_data) > 2:
        stdev_score = statistics.stdev(score_data)
    else:
        stdev_score = max(score_data) - min(score_data)

    leaderboard_msg = "```\nLeaderboard: \n"

    lb = get_leaderboard()
    for player in score_list:
        lb_player = lb.get_player(player)
        leaderboard_msg += f"{app.get_username_from_id(player)}: {lb_player.elo} -> "
        elo_add = 0
        if not stdev_score == 0:
            elo_add = round((30 * (score_list.get(player) - mean_score) / stdev_score))
        lb_player.elo += elo_add
        if lb_player.elo < 100:
            lb_player.elo = 100
        leaderboard_msg += f"{lb_player.elo} "
        if elo_add < 0:
            leaderboard_msg += f"({elo_add})\n"
        else:
            leaderboard_msg += f"(+{elo_add})\n"
    add_leaderboard(lb)

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
