#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

from common import Common

dir_file = "./configure/env_support.csv"


class ConfigureFileParsing(object):
    def __init__(self):
        print("Welcome to class ConfigureFileParsing")
        self.row = 0
        self.column = 0

    def get_suite_ower(self):
        common_fun = Common()
        date = common_fun.get_csv_data(dir_file)
        self.row = len(date)
        self.column = len(date[0])
        # print "row:{} column:{}".format(self.row, self.column)
        return date
