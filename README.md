# network_syslog_summary
Script to summarise Cisco syslog into top N talkers by message and device, graph total message count over last retention
period and post to Slack. Optionally, you can filter out noisy messages from the top ten devices.

The script is to aid daily operational checks in a busy NOC. 
Suggest it is run daily via cron.  

We have a `network_config` repo which contains all our global config files. Secrets are not sync'd to github. This repo contains instructions as to where to find the information needed to populate the config files in our environment. In time we'll make this public and link from here.

This script has two config files: `slack.json` - enables post to slack and `config.json` which contains variables only relevant to this script. The slack settings are global, script config settings are not. 

As such, the script assumes its configuration files are located, relative to this repo, as follows:

`/path/to/repos/network_syslog_summary/config.json`
`/path/to/repos/network_config/slack.json`
I've used relative paths in the script as I don't know where you'll clone the repo to.

Here is an example of how `slack.json` should look:
```
{
    "OAUTH_TOKEN_PROD": "your_token_here",
    "WEBHOOK_PROD": "https://hooks.slack.com/services/MY/PROD/WEBHOOK/PATH",
    "WEBHOOK": 0,
    "CHANNEL": "channel_name_no_hash",
}
```
Head to https://api.slack.com to generate your OAUTH token. 

Here is an example of how `config.json` should look:
```
{
	"USERNAME":"syslog_server_user_id",
	"SERVER":"syslog-srv.domain",
	"PATH":":/var/log/syslog-ng/path/to/syslog/",
	"DAYS": 30,
	"TOPTALKERS": 10,
	"LOCALPOST": 0,
	"IGNORE_LIST" : "MSG-ID-FOO,MSG-ID-BAR",
	"TIDY_OUTPUT": 1,
	"CRITICAL_LIST":"MSG-ID-BAZ,MSG-ID-BAM"
}
```
The first three are specific to your syslog server.
```
DAYS = number of days' data to retain and graph.
TOPTALKERS = how many messages to display. 
LOCALPOST = toggle local output or post to slack, useful for debugging. 
IGNORE_LIST = syslog message ID's you don't want to see
CRITICAL_LIST = syslog message ID'd you want to highlight.
```
Note:
1. We aggregate all our switch logs into a single ```switch.log``` file. You will need to do this.
2. network-syslog-summary takes the message-id and the name or IP of the device from each line and counts the total 
unique entries. 
3. These are sorted in reverse order for quick reference and posted to our slack channel in ```json``` format.
4. A graph is produced showing the previous RETENTION days' data for trend analysis. If you can use OAUTH this will 
also be posted to Slack

Historical data for RETENTION days is stored in history.json like this:
```json
{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195}
```

Output as follows:  

![Graph](https://github.com/guymorrell/network-syslog-summary/blob/master/myplot.png)

```
The top N messages across the whole network are:
('%message-id-foo:', 158364)
('%message-id-bar:', 76566)
...
('%message-id-baz:', 207)

The top 10 counts of device/message_id combinations are:
The top N talkers are:
('device-01.domain.com %message-id-foo:', 10362)
('device-02.domain.com %message-id-bat:', 10362)
...
('device-N.domain.com %message-id-bong:', 10362)
etc
```
## Running the script
### ssh
We run this script on our network automation server 'net-auto-srv'. It copies the file from our syslog server 'syslog-srv'. To simplify things we have a 'netadmin' account on each and use an rsa certificate for passwordless transfers. 
```
ssh-keygen -t rsa -b 4096 -C "netadmin@net-auto-srv.domain"
copy id_rsa.pub from net-auto-srv:/home/netadmin/.ssh/ to syslog-srv:/home/netadmin/.ssh/authorized_keys
```
Check you can ssh from net-auto-srv to syslog-srv as the netadmin user without a password before running the script.
### pipenv
We use python3 with [pipenv](https://docs.python-guide.org/dev/virtualenvs) to simplify dependencies. Our stock Centos build was missing pip. To get things up and running I did the following as the 'netadmin' user:
* `sudo yum install python-pip`
* Install [linuxbrew](https://docs.brew.sh/Homebrew-on-Linux)
* `brew install pipenv`
* `pipenv install matplotlib `
* `pipenv install requests`
* `pipenv install slackclient`
* `contab -e`

Cron needs to run the script from within the local directory for pipenv to have the right environment variables to run properly. Without this it will spin up a new virtual environment and then fail as no modules will have been installed. The Crontab looks like this:
```
59 07 * * *  cd /home/netadmin/network_syslog_summary/ && /home/linuxbrew/.linuxbrew/bin/pipenv run python network_syslog_summary.py  2>&1 /dev/null
```
Pipfile in `/home/netadmin/network_syslog_summary` looks like this:

```
[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]
matplotlib = "*"
requests = "*"
slackclient = "*"

[requires]
python_version = "3.6"
```
