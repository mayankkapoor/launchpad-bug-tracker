# launchpad-bug-tracker
Query launchpad's bug database and generate statistical information.

1. Execute shell
/var/lib/jenkins/scripts/check_link.sh;
direc=`ls -t /var/lib/jenkins/LPReports|head -1|awk '{print $1}'`;
ln -f -s /var/lib/jenkins/LPReports/$direc /var/lib/jenkins/LPReports/latest;

2. Execute shell
python /var/lib/jenkins/scripts/make_report.py

Publish Path:
/var/lib/jenkins/LPReports/latest/index.html

Notes: Make sure Apache and Jenkins servers are configured appropriately
