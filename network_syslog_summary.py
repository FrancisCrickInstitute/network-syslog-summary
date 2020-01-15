#!/usr/bin/env python
'''
Script to summarise Cisco syslog into top N talkers by message and device, graph total message
count over last retention period and post to Slack in json format.

Historical data for RETENTION days is stored in history.json like this:
{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195}

Output is a graph of historical data + today's count, and the following text:

The top N talkers are:
('device-01.domain.com %message-id-A:', 10362)
('device-02.domain.com %message-id-B:', 10362)
...
('device-N.domain.com %message-id-Z:', 10362)
etc

Guy Morrell 2019-06
'''
import os
import fnmatch
import datetime
from datetime import date, timedelta
import gzip
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import requests # module is called requests
import slack # module is called slackclient


global_count = {}
sorted_gmc = {}
message_count = {}
line_count = 0
now = datetime.datetime.now()
# YYYY-MM-DD
today_ymd = "switch.log-"+now.strftime("%Y")+"-"+now.strftime("%m")+"-"+now.strftime("%d")+".gz"
with open("server.json", "rt") as server_f:
    credentials = json.load(server_f)
USERNAME = credentials["USERNAME"]
SERVER = credentials["SERVER"]
PATH = credentials["PATH"]
RETENTION = int(credentials["DAYS"])
TALKERCOUNT = credentials["TOPTALKERS"]
USEWEBHOOK = credentials["WEBHOOK"] # set 1 in server.json if you can't use OATH (no graph though)
WEBHOOK_URL = credentials["WEBHOOK_PROD"]
DEBUG = credentials["LOCALPOST"] # set to 1 in server.json for local output & disable slack posting
OATH = credentials["OAUTH_TOKEN_BOT"]
SLACKCHANNEL = credentials["CHANNEL"]
SKIP = credentials["IGNORE_LIST"].split(",") # any messages we may skip
TIDY = credentials["TIDY_OUTPUT"]
CRITICAL = credentials["CRITICAL_LIST"].split(",") # messages which need immediate action
ARG = "scp " + USERNAME + "@" + SERVER + PATH + today_ymd+" ./"
today_d = date.today()
today_s = today_d.strftime("%Y-%m-%d")
oldest_d = today_d - timedelta(days=RETENTION)
oldest_s = oldest_d.strftime("%Y-%m-%d")

# Copy today's log from the syslog server
# Name format for yesterday's log is switch.log-YYYY-MM-DD.gz, where DD = today, as the
# rotation happens at 06:00. Need to cope with the script running multiple times in one
# day and should delete old logfiles

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

# Count unique message_id and store in global_count dict for network wide counts
# Combine message_id with hostname and and store in message_count dict for device specific counts

for line in log:
    line_count += 1
    # Grab the unique message id, e.g. %DOT1X-5-FAIL:
    line_list = line.strip().split()
    if len(line_list) > 8:
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
        # Now increment the global count of this message_id
        if message_id not in global_count:
            global_count[message_id] = 1
        else:
            global_count[message_id] += 1
# Create a reverse sorted list by global count of message_id's
sorted_gmc = sorted(global_count.items(), key=lambda x: x[1], reverse=1)
# Create a reverse sorted list by device count of message_id's
sorted_mc = sorted(message_count.items(), key=lambda x: x[1], reverse=1)

if DEBUG:
    print(today_ymd+"'s line count is "+str(line_count))
    for msg_id, counted in sorted_gmc:
        print(msg_id, ": ", counted)
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
            print("Only "+str(size)+" entries out of "+str(RETENTION)+" entries stored in history")
        else:
            print("    "+oldest_s+" not in history")
    # add today's count
    history[today_s] = line_count
    # Re-write history
    with open('history.json', 'w') as outfile:
        json.dump(history, outfile)

# Plot a graph of the last retention days' data (total syslog message count for trend analysis)
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

msgcount = TALKERCOUNT
# Produce the top TALKERCOUNT messages by count
messagestring = "The top "+str(TALKERCOUNT)+" messages across the whole network and with \n :warning: " \
                                            "*"+str(CRITICAL)+"* :warning: \n highlighted if found by count are:"
message_data = []
message_data.append({"type": "section", "text": {"type": "mrkdwn", "text": messagestring}})
for i in sorted_gmc:
    if msgcount > 0:
        match = 0
        for criticalmessage in CRITICAL:  # warn if current message i is on a watch list
            if re.search(str(criticalmessage), str(i)):
                match = 1
        if match == 1:
            message_data.append({'type': "section", "text": {"text": " :warning: * "+str(i).rstrip()+"*:warning:\n", "type": "mrkdwn"}})
        else:
            message_data.append({'type': "section", "text": {"text": str(i), "type": "mrkdwn"}})
        if DEBUG:
            print(i)
    msgcount -= 1
# Produce the top TALKERCOUNT messages by device
data = []
count = TALKERCOUNT
if TIDY:
    talkerstring = "The top " + str(TALKERCOUNT) + """ counts of device/message_id combinations
    excluding """+str(SKIP) +"are:"
    data.append({"type": "section", "text": {"type": "mrkdwn", "text": talkerstring}})
    for j in sorted_mc:
        # Ignore message IDs listed in SKIP
        match = 0
        for skippedmessage in SKIP: # ignore it if any element in SKIP matches the current message j
            if re.search(str(skippedmessage), str(j)):
                match = 1
        if match == 0: # only print if the message isn't in the list called 'SKIP'
            if count > 0:
                match2 = 0 # highlight critical log messages
                for criticalmessage in CRITICAL:  # warn if current message j is on a watch list
                    if re.search(str(criticalmessage), str(j)):
                        match2 = 1
                if match2 == 1:
                    data.append({'type': "section", "text": {"text": " :warning: *"+str(j).rstrip()+"*:warning:\n", "type": "mrkdwn"}})
                else:
                    data.append({'type': "section", "text": {"text": str(j), "type": "mrkdwn"}})
                if DEBUG:
                    print("SKIP hit")
                    print(j)
            count -= 1
else:
    talkerstring = "The top " + str(TALKERCOUNT) + " counts of device/message_id combinations are:"
    data.append({"type": "section", "text": {"type": "mrkdwn", "text": talkerstring}})
    for j in sorted_mc:
        if count > 0:
            data.append({'type': "section", "text": {"text": str(j), "type": "mrkdwn"}})
            if DEBUG:
                print("Skip miss)")
                print(j)
        count -= 1
def post_to_slack_webhook(message):
    """Post message to slack with error checking."""
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
client = slack.WebClient(token=OATH)

if DEBUG == 0:
    if USEWEBHOOK == 1:
        post_to_slack_webhook(message_data)
        post_to_slack_webhook(data)
    else:
        client.files_upload(
            channels=SLACKCHANNEL,
            file="plot.png",
            title="Daily checks graph"
        )
        client.chat_postMessage(
            channel=SLACKCHANNEL,
            blocks=message_data
        )
        client.chat_postMessage(
            channel=SLACKCHANNEL,
            blocks=data
        )
