sudo cp bash/gitcheck.sh /usr/local/bin/
(crontab -l ; echo "MAILTO=\"\"") | crontab -
(crontab -l ; echo "0 * * * * /usr/local/bin/gitcheck.sh") | crontab -
