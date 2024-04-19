DISCLAIMER: not very thoroughly tested, may or may not successfully work

to run on your own machine:

create secret.py file, and put 
```py
SLACK_BOT_TOKEN = <your Slack app token>
SLACK_SIGNING_SECRET = <your Slack app signing secret>
TBA_API_KEY = <your API key>
```

slack app required scopes:
```
chat:write
commands
groups:history
im:history
mpim:history
channels:history
users.profile:read
```

slack app required bot events to subscribe to:
```
message.channels
message.groups
message.im
message.mpim
```
