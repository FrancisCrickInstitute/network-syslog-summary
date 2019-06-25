# network-syslog-summary
Summarise syslog-ng format Cisco logs and graph count. Work in progress.
The script is to aid daily operational checks in a busy noc.
1. We aggregate all our switch logs into a single switch.log file
2. network-syslog-summary takes the message-id and the name or IP of the device from each line and counts the total unique entries. 
3. These are sorted in reverse order for quick reference. 
4. history.txt contains syslog ine counts from the last n days
5. The oldest entry is removed, today's is added and the result is graphed.
