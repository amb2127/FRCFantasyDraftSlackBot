import os
from slack_bolt import App

# Initialize your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Add functionality here later

# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
