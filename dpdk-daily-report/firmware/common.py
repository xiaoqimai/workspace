#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import os
import csv
import pandas as pd
from openpyxl import *


class Common(object):
    def __init__(self):
        print("Welcome to class Common")

    @staticmethod
    def get_csv_data(open_file):
        return_date = []
        with open(open_file) as file_descriptor:
            data = csv.reader(file_descriptor)
            for row in data:
                return_date.append(row)
        file_descriptor.close()
        return return_date

    @staticmethod
    def put_csv_data(open_file, list_data):
        row = len(list_data)
        with open(open_file, 'a') as file_descriptor:
            csv_write = csv.writer(file_descriptor, dialect='excel')
            for i in range(row):
                # print list_data[i]
                csv_write.writerow(list_data[i])
        file_descriptor.close()

    @staticmethod
    def change_csv_to_xlsx(csv_file, xlsx_file):
        if os.path.exists(csv_file):
            csv_file = pd.read_csv(csv_file, encoding='utf-8')
            if os.path.exists(xlsx_file):
                os.remove(xlsx_file)
            csv_file.to_excel(xlsx_file, sheet_name='data')
            wb = load_workbook(xlsx_file)
            ws = wb.active
            ws.delete_cols(1)
            wb.save(xlsx_file)
