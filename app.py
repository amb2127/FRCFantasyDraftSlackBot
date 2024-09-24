import datetime
import os
import re
import requests
import statbotics

import game
import secret
import leaderboard
from slack_bolt import App

# Initialize your app with your bot token and signing secret
app = App(
    token=secret.SLACK_BOT_TOKEN,
    signing_secret=secret.SLACK_SIGNING_SECRET
)


def get_username_from_id(user_id: str) -> str:
    return app.client.users_profile_get(user=user_id)['profile']['first_name']


def check_if_event_finished(event_code: str) -> bool:
    url = "https://www.thebluealliance.com/api/v3/event/" + event_code + "/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)
    data = r.json()

    return datetime.date.today() > datetime.datetime.strptime(data['end_date'], "%Y-%m-%d").date()


def process_team_data(team_num: int):
    year = datetime.date.today().year

    url = "https://www.thebluealliance.com/api/v3/team/frc" + str(team_num)
    district_url = "https://www.thebluealliance.com/api/v3/team/frc" + str(team_num) + "/districts"
    events_url = "https://www.thebluealliance.com/api/v3/team/frc" + str(team_num) + "/events/" + str(year) + "/simple"
    params = {"X-TBA-Auth-Key": secret.TBA_API_KEY}

    r = requests.get(url=url, params=params)
    data = r.json()

    sb = statbotics.Statbotics()
    epa = sb.get_team_year(team_num, year)['epa_end']

    district_r = requests.get(url=district_url, params=params)
    district_data = district_r.json()

    if len(district_data) > 0:
        district_name = district_data[0]['display_name']
    else:
        district_name = "N/A"

    event_r = requests.get(url=events_url, params=params)
    event_data = event_r.json()

    events = ""

    if event_data is not None:
        event_data = sorted(event_data, key=lambda x: x['start_date'])
        for event in event_data:
            events += "\n" + event['name']

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Team {team_num} - {data['nickname']}*"
            },
            "accessory": {
                "type": "image",
                "image_url": f"https://frcavatars.herokuapp.com/get_image?team={str(team_num)}",
                "alt_text": str(team_num)
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Location:*\n{data['city']}, {data['state_prov']}, {data['country']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Rookie Year:*\n{data['rookie_year']}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Website:*\n<{data['website']}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*District:*\n{district_name}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Events:*{events}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*EPA:*\n{epa}"
                }
            ]
        }
    ]

    return blocks


@app.command("/new_game")
def create_new_game(ack, say, command):
    ack()

    if str(command['text']).count(" ") == 1:
        event_code, max_teams = str(command['text']).split()
    elif str(command['text']).count(" ") == 0:
        event_code = command['text']
        max_teams = 4
    else:
        say("Invalid command args!")
        return

    new_game = game.Game(game.get_team_list_from_event(event_code), [],
                         command['user_id'], command['channel_name'], event_code, int(max_teams))
    say(f"<@{command['user_id']}> has started a new game with event {event_code}!"
        f"\nID: {new_game.game_id}\nPicks: {max_teams}")

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

    if game.game_list.get(int(command['text'])).started:
        say("Game already started!")
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

    if cur_game.host_uid != command['user_id']:
        say("You are not the host of this game!")
        return

    if not cur_game.start():
        say("Game already started!")
        return

    say(f"Game {command['text']} has started!")
    say(cur_game.get_players())
    say(cur_game.get_up_next_msg())
    say(cur_game.get_available_teams())


@app.command("/team_info")
def post_team_info(ack, say, command):
    ack()

    if re.match("^[0-9]+$", command['text']) is None:
        say("Invalid team number")
        return

    blocks = process_team_data(int(command['text']))

    say(blocks=blocks, text=f"Team {command['text']} Info", unfurl_links=False)


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

    if not check_if_event_finished(cur_game.event_code):
        say("Event has not finished yet!")
        return

    scores, lb = cur_game.calculate_scores_and_print()

    if scores is not None:
        game.delete(cur_game.game_id)
        say(scores)
        say(lb)


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
    if not os.path.isfile("./leaderboard.txt"):
        leaderboard.add_leaderboard(leaderboard.LB([]))

    app.start(port=int(os.environ.get("PORT", 3000)))
