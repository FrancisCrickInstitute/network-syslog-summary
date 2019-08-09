# network-syslog-summary
Script to summarise Cisco syslog, graph total message count over last retention period and post to Slack.

Historical data for RETENTION days is stored in history.json like this:
```json
{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195}
```
The script is to aid daily operational checks in a busy NOC. Suggest it is run daily via cron.  
Rename server_example.json to server.json locally and add your details.
1. We aggregate all our switch logs into a single switch.log file
2. network-syslog-summary takes the message-id and the name or IP of the device from each line and counts the total unique entries. 
3. These are sorted in reverse order for quick reference and posted to our slack channel
4. A graph is produced showing the previous N days' data for trend analysis. If you can use OAUTH this will also be posted to slack

Output is a graph of historical data + today's count, and the following text (sent to slack in json format):  

![Graph](https://github.com/guymorrell/network-syslog-summary/blob/master/myplot.png)

```
The top talkers are:
('device-01.domain.com %message-id-A:', 10362)
('device-02.domain.com %message-id-B:', 10362)
...
('device-N.domain.com %message-id-Z:', 10362)
etc
```

