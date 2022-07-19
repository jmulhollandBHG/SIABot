Dependencies
1) pip install python-dotenv
2) pip install slackclient
3) If running SIA locally. 
3a) pip install flask
3b) python SIA.py
3c) Install ngrok(https://ngrok.com/download)
3d) cd into the directory holding ngrok.exe
3e) 'ngrok http PORT' port is whatever port is the current active port. Current PORT is 5000.
3f) Under the free version of ngrok, this must be done everytime. Copy the forwarding address and paste it into api.slack.com/apps/<app_id>/event-subscriptions?, into request url. Add /slack/events to the end of the url. For example ("https://b77e-108-5-56-212.ngrok.io/slack/events")
4) If running SIA serverside.


