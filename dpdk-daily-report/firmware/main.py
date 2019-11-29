#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import os
import sys
from dr import DailyReport

os.chdir("../")
cwd = os.getcwd()
sys.path.append(cwd + '/firmware')
sys.path.append(cwd + '/library')
sys.path.append(cwd + '/configure')


def main():
    daily_report = DailyReport()
    daily_report.get_daily_report()


if __name__ == '__main__':
    main()
