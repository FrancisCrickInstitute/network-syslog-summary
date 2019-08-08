# network-syslog-summary
Summarise syslog-ng format Cisco logs and graph count. Work in progress.
The script is to aid daily operational checks in a busy NOC.
Rename server_example.json to server.json locally and add your details. 
1. We aggregate all our switch logs into a single switch.log file
2. network-syslog-summary takes the message-id and the name or IP of the device from each line and counts the total unique entries. 
3. These are sorted in reverse order for quick reference and posted to our slack channel
4. A graph is produced showing the previous N days' data for trend analysis. I'm working on posting this to slack too.

Output as follows (graph not shown but example is available in this repo):

switch.log-2019-07-17.gz's line count is 260459

Count of loglines per day over last 7 days is:

{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195, '16-Jul': 291950, '17-Jul': 260459}

Top 20 talkers are: (this bit is obfruscated)

('device_1 %MSG_A:', COUNT)

('device_2 %MSG_B:', COUNT)

etc
