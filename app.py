import os
import re

import game
import secret
from slack_bolt import App

# Initialize your app with your bot token and signing secret
app = App(
    token=secret.SLACK_BOT_TOKEN,
    signing_secret=secret.SLACK_SIGNING_SECRET
)


def get_username_from_id(user_id: str) -> str:
    return app.client.users_profile_get(user=user_id)['profile']['first_name']


@app.command("/new_game")
def create_new_game(ack, say, command):
    ack()

    new_game = game.Game(game.get_team_list_from_event(command['text']), [],
                         8, command['user_id'], command['channel_name'], command['text'])
    say(f"<@{command['user_id']}> has started a new game with event {command['text']}!\nID: {new_game.game_id}")

    say(new_game.get_players())
    say(new_game.get_available_teams())

    say("Use /join_game [game_id] to join the game!")


@app.command("/end")
def end_game(ack, say, command):
    ack()

    if re.match("^[0-9]+$", command['text']) is None:
        say("Invalid game ID")
        return

    game.delete(int(command['text']))

    say(f"Game ID {command['text']} has been deleted.")


@app.command("/join_game")
def join_game(ack, say, command):
    ack()

    if re.match("^[0-9]+$", command['text']) is None:
        say("Invalid game ID")
        return

    if int(command['text']) not in game.game_list:
        say("Game not found!")
        return

    user = game.Player(get_username_from_id(command['user_id']), command['user_id'])

    for i in game.game_list:
        if game.game_list[i].get_player(command['user_id']) is not None:
            say("You are already in a game!")
            return

    game.game_list.get(int(command['text'])).add_player(user)
    say(f"<@{command['user_id']}> has joined game {command['text']}!")
    say(game.game_list.get(int(command['text'])).get_players())
    return


@app.command("/game_list")
def list_games(ack, say):
    ack()

    games = ""

    for cur_game in game.game_list:
        games += f"Game ID: {game.game_list[cur_game].game_id}\n"

    say(games)


@app.command("/start")
def start_game(ack, say, command):
    ack()

    if re.match("^[0-9]+$", command['text']) is None:
        say("Invalid game ID")
        return

    if int(command['text']) not in game.game_list:
        say("Game not found!")
        return

    cur_game = game.game_list.get(int(command['text']))

    if not cur_game.start():
        say("Game already started!")
        return

    say(f"Game {command['text']} has started!")
    say(cur_game.get_players())
    say(cur_game.get_up_next_msg())
    say(cur_game.get_available_teams())


@app.command("/scores")
def get_scores(ack, say, command):
    ack()

    if re.match("^[0-9]+$", command['text']) is None:
        say("Invalid game ID")
        return

    if int(command['text']) not in game.game_list:
        say("Game not found!")
        return

    cur_game = game.game_list.get(int(command['text']))

    if not cur_game.completed:
        say("Cannot score an incomplete game!")
        return

    scores = cur_game.calculate_scores_and_print()

    if scores is not None:
        game.delete(cur_game.game_id)
        say(scores)


@app.message(re.compile("^[0-9]+$"))
def make_pick(ack, message, say):
    ack()

    for i in game.game_list:
        if not game.game_list[i].started:
            continue
        if game.game_list[i].get_player(message['user']) is not None:
            cur_game = game.game_list[i]
            user = cur_game.get_player(message['user'])

            if cur_game.up_next[0] != user:
                return

            if cur_game.add_pick(int(message['text']), user.uid):
                say(f"<@{message['user']}> has picked {message['text']}!")
                cur_game.up_next.pop(0)

                if len(cur_game.up_next) == 0:
                    say("Draft complete!")
                    say(cur_game.get_players())
                    cur_game.end()
                    return

                say(cur_game.get_players())
                say(cur_game.get_up_next_msg())
                say(cur_game.get_available_teams())
            else:
                say("Invalid pick!")


@app.message(re.compile("^[0-9]+ [0-9]+$"))
def make_double_pick(ack, message, say):
    ack()

    for i in game.game_list:
        if not game.game_list[i].started:
            continue
        if game.game_list[i].get_player(message['user']) is not None:
            cur_game = game.game_list[i]
            user = cur_game.get_player(message['user'])

            if len(cur_game.up_next) < 2:
                return

            if cur_game.up_next[0] != user or cur_game.up_next[1] != user:
                return

            picks = message['text'].split(" ")

            if cur_game.add_pick(int(picks[0]), user.uid):
                if cur_game.add_pick(int(picks[1]), user.uid):
                    say(f"<@{message['user']}> has picked {picks[0]} and {picks[1]}!")
                    cur_game.up_next.pop(0)
                    cur_game.up_next.pop(0)

                    if len(cur_game.up_next) == 0:
                        say("Draft complete!")
                        say(cur_game.get_players())
                        cur_game.end()
                        return

                    say(cur_game.get_players())
                    say(cur_game.get_up_next_msg())
                    say(cur_game.get_available_teams())
                else:
                    say(f"<@{message['user']}> has picked {picks[0]}, but {picks[1]} is an invalid pick!")
                    cur_game.up_next.pop(0)

                    say(cur_game.get_players())
                    say(cur_game.get_up_next_msg())
                    say(cur_game.get_available_teams())
            else:
                say("Invalid picks!")


# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
