#!/bin/bash
# /etc/profile.d/services.sh
# #########################################################################
# Heads Up Services Display
# -- by Justin J. Novack
# Purpose: Print running services on startup for ease of information
#
# Changelog:
#            Jun 12, 2015 - Fixed need to modify script for unused services
#            Aug 19, 2014 - First release

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# Remove the services that are not started on this box.
services=(
    "httpd"
    "nginx"
    "nginx-statsd"
    "elasticsearch"
    "kibana"
    "mariadb"
    "mysql"
    "postgresql"
    "memcached"
    "redis"
    "keepalived"
    "haproxy"
    "dummy"
    "carbon"
    "statsd"
    "collectd"
    "ntpd"
    "jabber-alerts"
    "osad"
    "bitbucket"
    "bamboo"
    "docker"
    "tftp"
    "sec@"
);

# Set up color greps for highlight only
alias highlight-red="GREP_COLOR='1;31' grep --line-buffered --color=always -C 10000"
alias highlight-green="GREP_COLOR='1;32' grep --line-buffered --color=always -C 10000"
alias highlight-yellow="GREP_COLOR='1;33' grep --line-buffered --color=always -C 10000"
alias highlight-blue="GREP_COLOR='1;34' grep --line-buffered --color=always -C 10000"
alias highlight-purple="GREP_COLOR='1;35' grep --line-buffered --color=always -C 10000"
alias highlight-cyan="GREP_COLOR='1;36' grep --line-buffered --color=always -C 10000"
alias highlight-white="GREP_COLOR='1;37' grep --line-buffered --color=always -C 10000"

# Local IP Address
IPADDR=`hostname --ip-address`

# Create and export our prettyprint function
prettyprint() { highlight-white -E '^|[a-zA-Z0-9_.-\@]+.service' | highlight-green -E '^| active|running|\bUP\b|OPEN|MASTER|\bUp\b|\bHIT\b' | highlight-yellow -E '^|BACKUP|\bUPDATING\b' | highlight-red -E '^| inactive|dead|failed|DOWN|FAULT|Exited|\bMISS\b|\bEXPIRED\b'; }
export -f prettyprint

checkservices() {
echo
# Loop through the services
for service in "${services[@]}"; do
    RET=`systemctl is-enabled $service 2>/dev/null`
    if [ "$?" == "0" ] ; then
        systemctl status $service | head -5 | grep -vE '^$|Loaded:|Drop:|PID:|Process:|Docs:|─|CGroup:|Memory:|\bman\b' | prettyprint
    fi
done
}
export -f checkservices

checkhaproxy() {
  if [ -S /var/lib/haproxy/stats ]; then
    echo
    echo "Cluster Name      Cluster Node      State   Status    Last Check" | highlight-white -E '.'
    echo "show stat" | nc -U /var/lib/haproxy/stats | awk '{ FS = ","; print sprintf("%-16s  %-16s  %-6s  %-8s  %s", $1, $2, $18, $37, $57)}' | grep -v 'pxname' | prettyprint
  fi
}
export -f checkhaproxy

checkkeepalived() {
  if [ -a /var/run/keepalived.pid ]; then
    echo
    echo -n "keepalived.service is" `cat /tmp/keepalived.*` | prettyprint
  fi
}
export -f checkkeepalived

checkelasticsearch() {
    if [ -a /var/run/elasticsearch/elasticsearch.pid ]; then
        ESSTAT=`curl -sL http://${IPADDR}:9200/_cluster/health | grep -Po '"status":.*?,' | sed -e 's/.*:\"\?\(\w*\)\"\?,/\1/' | highlight-red -E '^|red' | highlight-yellow -E '^|yellow' | highlight-green -E '^|green'`
        ESSERV=`curl -sL http://${IPADDR}:9200/_cluster/health | grep -Po '"number_of_nodes":.*?,' | sed -e 's/.*:\"\?\(\w*\)\"\?,/\1/' | highlight-red -E '^|1' | highlight-yellow -E '^|2' | highlight-green -E '^|3'`
        echo
        echo "${bldwht}ElasticSearch${reset} health is ${ESSTAT}, there are ${bldylw}${ESSERV}${reset} servers in the cluster."
    fi
}
export -f checkelasticsearch

checkuptime() {
    echo
    echo -n Uptime:
    uptime
}
export -f checkuptime

checknginx() {
    if [ -a /var/run/nginx.pid ]; then
        echo
        echo "${bldwht}nginx${reset} is currently hosting the following websites:"
        ls -1 /etc/nginx/sites-enabled/*.conf | awk -F '/' '{print $5}' | sed -e 's/.conf//g' | sed -e 's/^/   /g' | highlight-cyan .
    fi
}

checkdocker() {
    if [ -a /var/run/docker.pid ]; then
        echo
        echo "${bldwht}Docker${reset} containers:"
        docker ps -a --format "table \t{{.Names}}\t\t{{.Image}}\t{{.Status}}\t{{.ID}}" | prettyprint
    fi
}

if [ -a /etc/sysconfig/rhn/systemid ]; then
    echo
    echo ${yellow}~~ ${bldylw}NOTE ${reset}${yellow}~~ ${reset}This server is managed by ${bldgrn}spacewalk.phillypark.net${reset}.
    if [ $(find /etc/cron.* -name reboot.cron | wc -l) -eq 1 ]; then
        echo ${yellow}~~ ${bldylw}NOTE ${reset}${yellow}~~ ${reset}This server is set to reboot every $bldgrn$(find /etc/cron.* -name reboot.cron | awk -F"/" '{print $3}' | sed -e "s/cron.//g")${reset}.
    fi
fi

if [ $UID -eq 0 ]; then
    checkservices
    checknginx
    checkhaproxy
    checkkeepalived
    checkelasticsearch
    checkdocker
    checkuptime
    echo
fi
