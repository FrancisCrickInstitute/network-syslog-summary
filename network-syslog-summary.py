'''
 Script to summarise Cisco syslog and graph count over last retention period
 Output as follows:

switch.log-2019-07-17.gz's line count is 260459

Count of loglines per day over last 7 days is:
{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195, '16-Jul': 291950, '17-Jul': 260459}

Top 20 talkers are: (this bit is obfruscated)
('device_1 %MSG_A:', COUNT)
('device_2 %MSG_B:', COUNT)
etc

 Guy Morrell 2019-06
'''
import os
import fnmatch
import matplotlib.pyplot as plt
import numpy as np
import gzip
import json
import datetime
import requests
import slack
from datetime import date, timedelta


message_count = {}
line_count = 0
now = datetime.datetime.now()
today_ymd = "switch.log-"+now.strftime("%Y")+"-"+now.strftime("%m")+"-"+now.strftime("%d")+".gz"# YYYY-MM-DD
with open("server.json", "rt") as server_f:
    credentials = json.load(server_f)
USERNAME = credentials["USERNAME"]
SERVER = credentials["SERVER"]
PATH = credentials["PATH"]
RETENTION = int(credentials["DAYS"])
USEWEBHOOK = 0 # set true if you can't use OATH, no graph with webhooks
WEBHOOK_URL = credentials["WEBHOOK_PROD"]
OATH = credentials["OAUTH_TOKEN_BOT"]
ARG = "scp " + USERNAME + "@" + SERVER + PATH + today_ymd+" ./"
DEBUG =0 # set to 1 for extra output and to disable slack posting
today_d = date.today()
today_s = today_d.strftime("%Y-%m-%d")
oldest_d = today_d - timedelta(days = RETENTION)
oldest_s = oldest_d.strftime("%Y-%m-%d")
'''
Copy today's log from the syslog server
Name format for yesterday's log is switch.log-YYYY-MM-DD.gz, where DD = today, as the rotation happens at 06:00
Need to cope with the script running multiple times in one day and should delete old logfiles
'''
if not os.path.exists(today_ymd):
    print("Copying file")
    os.system(ARG) # copy yesterday's file to the local folder
    update_hist = 'true'
with gzip.open(today_ymd, mode='rt') as f:
    log = f.readlines()
# delete any filenames starting switch.log except today's
for filename in os.listdir():
    if fnmatch.fnmatch(filename, 'switch.log*'):
        if not fnmatch.fnmatch(filename, today_ymd):
            os.remove(filename)
# Count unique messaage_id / name combined messages and store in message_count dict
for line in log:
    line_count += 1
    # Grab the unique message id, e.g. %DOT1X-5-FAIL:
    message_id = line.strip().split()[9]
    # Grab the name or IP of the device
    device_id = line.strip().split()[3]
    # Combine for easy counting
    device_message = device_id + " " + message_id
    if device_message not in message_count:
        message_count[device_message] = 1
    else:
        count = message_count[device_message]
        count += 1
        message_count[device_message] = count
if DEBUG:
    print(today_ymd+"'s line count is "+str(line_count))
# Read the old history file
if os.path.exists("history.json"):
    with open("history.json", "rt") as history_f:
         history = json.load(history_f)
    if DEBUG:
        print("Count of loglines per day over last "+str(RETENTION)+" days is:")
        print(history)
else:
    print("No history file found.")
# find oldest date and update variable
date_list = []
for date in history.keys():
    date_list.append(date)
date_list.sort() # be sure oldest is in element 0
oldest_s = str(date_list[0])
# only overwrite if we don't yet have an entry for today
if today_s not in history:
    print("Updating history data")
    # get rid of the oldest entry if exists and we have at least retention entries
    size = len(history)
    if oldest_s in history and size >= RETENTION:
        print("Removing oldest entry, ", oldest_s)
        (history.pop(oldest_s))
    else:
        print("No deletion today: ")
        if size < RETENTION:
            print("     Only "+str(size)+" entries out of "+str(RETENTION)+" entries stored in history")
        else:
            print("    "+oldest_s+" not in history")
    # add today's count
    history[today_s] = line_count
    # Re-write history
    with open('history.json', 'w') as outfile:
        json.dump(history, outfile)

# Plot a graph of the last retention days' data
pos = 0
x_axis = []
y_axis = []
for date in history:
    x_axis.insert(pos, date)
    y_axis.insert(pos, history[date])
    pos += 1
plt.xlabel('Date')
plt.ylabel('Log Count')
np_history = np.array(y_axis, dtype=np.int64)
plt.title('Syslog Message Count over time')
plt.xticks(rotation=30)
plt.plot(x_axis, np_history)
if DEBUG:
    plt.show()
plt.savefig("plot.png")

# Print the top 20 messages by device
sorted_mc = sorted(message_count.items(), key=lambda x: x[1], reverse=1)
count = 20

data = []
data.append({"type": "section","text": {"type": "mrkdwn","text": "The top talkers are:"}})
if DEBUG:
    print("Top "+str(count)+" talkers are: ")
for i in sorted_mc:
    if count > 0:
        num = 21 - count
        data.append({'type': "section", "text": {"text": str(sorted_mc[num]), "type": "mrkdwn"}})
        if DEBUG:
            print(i)
    count -= 1

with open('message.json', 'wt') as message_f:
    json.dump(data, message_f, indent=4)

# Message should be a valid dict or list https://api.slack.com/tools/block-kit-builder
def post_to_slack_webhook(message):
    slack_data = json.dumps({'blocks': message})
    response = requests.post(
        WEBHOOK_URL, data=slack_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )

# If you can use OATH, you'll get the graph too. Use one or the other

# 'data' needs to be a valid dict or list https://api.slack.com/tools/block-kit-builder
slack_token = OATH
client = slack.WebClient(token=slack_token)

if USEWEBHOOK == 1:
    post_to_slack_webhook(data)
else:
    client.files_upload(
        channels="its-networks",
        file="plot.png",
        title="Daily checks graph"
    )
    client.chat_postMessage(
        channel="its-networks",
        blocks=data
    )





