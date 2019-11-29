#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import os
import csv


class BigData(object):
    def __init__(self):
        print("Welcome to class BigData")

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
                csv_write.writerow(list_data[i])
        file_descriptor.close()

    def get_all_data(self):
        old_file = './output/all_result.csv'

        if os.path.exists(old_file):
            data = self.get_csv_data(old_file)
            return data
        else:
            pass

    def get_tpye_data(self, type, date):
        data = self.get_all_data()
        put_file = '{}_{}_result.csv'.format(date, type)
        all_sys = []
        all_data = []

        for row in data:
            print row
            sys_tpye = '{}-{}-{}-{}-{}-{}'.format(row[0], row[2], row[3], row[1])
            if sys_tpye not in all_sys:
                all_sys.append(sys_tpye)

        for i in range(0, len(all_sys)):
            tmp_data = []
            tmp_data.append(all_sys[i])
            for j in range(0, date):
                tmp_data.append(0)
            all_data.append(tmp_data)

        for row_data in data:
            sys_type_data = '{}-{}-{}-{}-{}-{}'.format(row_data[0], row_data[2], row_data[3], row_data[1])
            for index in range(0, len(all_sys)):
                if sys_type_data == all_sys[index]:
                    for j in range(6, len(row)):
                        if (len(row) - 6) < len(all_data[0]):
                            if type == row[j]:
                                all_data[index][j - 6] = all_data[index][j - 6] + 1
                        else:
                            continue

        self.put_csv_data(put_file, all_data)

if __name__ == '__main__':
    run = BigData()
    run.get_tpye_data('Not Run', 10)

