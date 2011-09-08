#!/bin/bash
# growl.sh
#
###############################################################################
# iTerm2 Growl Integration
# -- 09/08/11 by Justin J. Novack
# 
# Purpose:
#   Adds growl() function for bash statements for custom alerting.
# Documentation:
#   echo "source growl.sh" >> .profile
# Use:
#   make && make install && growl Finally!

growl() { echo -e $'\e]9;'${1}'\007' ; return ; }
