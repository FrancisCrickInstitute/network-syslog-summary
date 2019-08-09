# network-syslog-summary
Summarise syslog-ng format Cisco logs and graph count.  

The script is to aid daily operational checks in a busy NOC. Suggest it is run daily via cron.  
Rename server_example.json to server.json locally and add your details.
1. We aggregate all our switch logs into a single switch.log file
2. network-syslog-summary takes the message-id and the name or IP of the device from each line and counts the total unique entries. 
3. These are sorted in reverse order for quick reference and posted to our slack channel
4. A graph is produced showing the previous N days' data for trend analysis. If you can use OAUTH this will also be posted to slack

Output as follows:

![title](https://github.com/guymorrell/network-syslog-summary/blob/master/myplot.png)

```
The top talkers are:
('device-01.domain.com %message-id-A:', 10362)
('device-02.domain.com %message-id-B:', 10362)
...
('device-N.domain.com %message-id-Z:', 10362)
etc
```

