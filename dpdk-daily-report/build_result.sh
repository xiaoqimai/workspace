#!/bin/bash
#
#Analysis of daily test reports and summary of test results
#Version 1.0
#
#Chen Bo
#2019-8-30


projectPath=$(cd `dirname $0`; pwd)
starttime=$(date +%Y-%m-%d\ %H:%M:%S)
echo $starttime
echo $projectPath
cd $projectPath
cd firmware
python main.py


