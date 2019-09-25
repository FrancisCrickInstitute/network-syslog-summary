# network-syslog-summary
Script to summarise Cisco syslog into top N talkers by message and device, graph total message count over last retention
period and post to Slack 

The script is to aid daily operational checks in a busy NOC. 
Suggest it is run daily via cron.  Rename server_example.json to server.json locally and add your details.

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
You'll want to check you can ssh from net-auto-srv to syslog-srv as the netadmin user without a password before running the script.
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
59 07 * * *  cd /home/netadmin/network-syslog-summary/ && /home/linuxbrew/.linuxbrew/bin/pipenv run python network-syslog-summary.py  2>&1 /dev/null
```
Pipfile in `/home/netadmin/network-syslog-summary` looks like this:

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
