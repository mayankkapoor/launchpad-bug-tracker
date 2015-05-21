#!/bin/bash

FILE="/var/lib/jenkins/LPReports/latest"

if [[ ! -a $FILE ]]; then
    rm -rf $FILE
fi

if [[ -L $FILE ]]; then
   rm -rf $FILE
fi

