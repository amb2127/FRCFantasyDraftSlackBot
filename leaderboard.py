import app
import pickle


class LBEntry:
    def __init__(self, uid: str, elo: int):
        self.uid = uid
        self.elo = elo

    def __str__(self):
        return f"{app.get_username_from_id(self.uid)}: {self.elo}"


def get_leaderboard() -> list[LBEntry]:
    with open("leaderboard.txt", "rb") as f:
        lb = pickle.load(f)
    return lb


def leaderboard_to_string(lb: list[LBEntry]):
    lb_str = "```\nLeaderboard:\n"
    for i in lb:
        lb_str += str(i) + "\n"
    lb_str += "```"
    return lb_str


def add_leaderboard(lb: list[LBEntry]):
    with open("leaderboard.txt", "wb") as f:
        pickle.dump(lb, f)

