from multiprocessing import Process
import signal
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import atexit

#Variables that will need to be changed once moved to an env.
SIA_DEFAULT_CHANNEL = '#general'
SIA_DEFAULT_CHANNEL_ID = 'C03P3BR3VMY'
PATH_TO_SCRIPT = 'C:/Users/jmulholland/Desktop/mobile1-server/scripts/ServerInfrastructureAnalysis/script.py'
PATH_TO_DEV_KEY = 'C:/Users/jmulholland/.ssh/dom-dev.pem'
PATH_TO_PROD_KEY = 'C:/Users/jmulholland/.ssh/dom-live.prod.pem'
PATH_TO_JSON = 'C:/BHG/sheets_editor_secret.json'
SLACK_TOKEN= 'xoxb-3785399091058-3796857550420-aMiToHCNERe72J8CE2nSus3V'
SIGNING_SECRET= 'c9203abbeb7665083cacd94e75ee04bb'

SIA_RUN_COMMAND = r'python ' + PATH_TO_SCRIPT + ' ' + PATH_TO_DEV_KEY + ' ' + PATH_TO_PROD_KEY + ' ' + PATH_TO_JSON

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    SIGNING_SECRET, '/slack/events', app)

client = slack.WebClient(token=SLACK_TOKEN)

def killSIA():
    try:
        with open('SIA_running.txt') as f:
                currPID = f.readlines()[0]
        os.kill(int(currPID), signal.SIGTERM) 
        os.remove('SIA_running.txt')
        return True
    except:
        return False

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    text = event.get('text')
    if text.startswith('!SIA'):
        if(text.__eq__('!SIA help')):
            client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'Please type \'!SIA ENV\', where ENV is the name of the ENV you would like to analyze. \n If you\'d like to analyze all available ENVs please type \'!SIA all\'. \n The results of the script will be posted into the Server Environments Google Spreadsheet.\n Typing \'!SIA kill\' will terminate all active processes of SIA. Allowing you to run the SIAScript if you received the message \'SIA Script is already running, please try again later.\' \n Typing \'SIA hello\' will give a response back to ensure SIA is online, no response = offline. \n NOTE: it takes around 3 minutes per environment, with all environments taking ~1 hour. I will update you when it is complete!')
        elif(text.__eq__('!SIA kill')):
            if(killSIA()):
                client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script has been terminated.')
            else:
                client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA was not running or failed to terminate.')
        elif(text.__eq__('!SIA hello')):
            client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'Hello!')
        else:
            SIA_run(text)

def SIA_run(command):
    #If the process is already running, don't start a new one
    if(not os.path.exists('SIA_running.txt')):
        env = getEnvFromStr(command)
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'Running the SIA Script')
        #Commas need to signify the env as a tuple instead of individual characters as arguments.
        p = Process(target=runSIAScript, args = (env,))
        p.daemon = True
        p.start()
        with open('SIA_running.txt', 'w') as f:
            f.write(str(p.pid))
    else:
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script is already running, please try again later.')

#Gets the env which should be on the space after the '!SIA', then if it is in http: format removes the http formatting.
def getEnvFromStr(command):
    command = command.split(' ')[1]
    if('|' in command):
        command = command.split('|')[1]
        command = command.replace('>', '')
    return command

def runSIAScript(env):
    #Gets the exit code from the SIA script.
    exit_code = os.system(SIA_RUN_COMMAND + ' ' + env)
    if(exit_code.__eq__(0)):
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script on ' + env + ' has completed.')
    elif(exit_code.__eq__(1)):
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script on ' + env + ' has failed connecting to Bastion.')
    elif(exit_code.__eq__(2)):
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script on ' + env + ' has failed to find your environment.')
    else:
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIA Script on ' + env + ' has failed due to an unexpected error.')
    os.remove('SIA_running.txt')

#Precaution incase SIABot goes down during a SIAScript run. 
def exit_handler(signum, frame):
    #When 'os.kill(os.getpid(), signal.SIGTERM)' is ran it will run the exit handler function. We do not need to do the functions in the conditional a second time. 
    if(not signum.__eq__(signal.SIGTERM)):
        killSIA()
        client.chat_postMessage(channel = SIA_DEFAULT_CHANNEL, text = 'SIABot has been terminated.')
    os.kill(os.getpid(), signal.SIGTERM)

signal.signal(signal.SIGINT, exit_handler)




if __name__ == '__main__':
    app.run(debug=True)