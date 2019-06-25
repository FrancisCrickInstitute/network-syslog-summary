'''
 Script to summarise Cisco syslog
 Guy Morrell 2019-06
'''
import os
import matplotlib.pyplot as plt
import numpy as np

message_count = {}
line_count = 0
history = []
history_output = ""
# Need to change this to open today's log from the syslog server
if os.path.exists("switch.log"):
    log = open("switch.log")
else:
    print("No logfile found")
for line in log:
    line_count += 1
    # Grab the unique message id, e.g. %DOT1X-5-FAIL:
    message_id = line.strip().split()[9]
    # Grab the name or IP of the device
    device_id = line.strip().split()[3]
    # Combine for easy counting
    device_message = device_id + " " + message_id
    # Count the combined messages and store in dict
    if device_message not in message_count:
        message_count[device_message] = 1
    else:
        count = message_count[device_message]
        count += 1
        message_count[device_message] = count
# Baseline count - need to store this in a file for future plotting
# List of last 7 days' counts [1,2,3,4,5,5,7]
if os.path.exists("history.txt"):
    with open("history.txt", "rt") as history_f:
        history_str = history_f.read()
        history = history_str.split(",")
#    os.remove("history.txt")
    print(history)
else:
    print("No history file found.")
# pop oldest entry, push newest on
(history.pop())
# add today's count to the start
history.insert(0, line_count)
# Re-write history
index = len(history) - 1
count = 0
with open("history_new.txt", "w") as history_f:
    for the_int in history:
        count += 1
        # print(the_int, file=history_f)
        history_output = history_output + str(the_int)
        if count <= index:
            history_output = history_output + ", "
    print(history_output, file=history_f)
# Plot a graph of the last 7 days' data
x_axis = [-6, -5, -4, -3, -2, -1, 0]
plt.xlabel('Date')
plt.ylabel('Log Count')
np_history = np.array(history, dtype=np.int64)
plt.title('Syslog Message Count over time')
plt.plot(x_axis, np_history)
plt.show()
# Print the top 20 messages by device
sorted_mc = sorted(message_count.items(), key=lambda x: x[1], reverse=1)
count = 20
for i in sorted_mc:
    if count > 0:
        print(i)
    count -= 1
