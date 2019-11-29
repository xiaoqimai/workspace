#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import os
import re
import codecs
import pandas as pd
from common import Common

result_file = "./output/all_result.csv"
xlsx_file = "./report/all_result.xlsx"
display_env_state = './output/env_state.csv'
display_env_xlsx = "./report/env_state.xlsx"
display_env_html = "./report/env_state.html"
display_suite_state = './output/suite_state.csv'
display_suite_xlsx = "./report/suite_state.xlsx"
display_suite_html = "./report/suite_state.html"


class GenerateReport(object):
    def __init__(self):
        print("Welcome to class GenerateReport")

    def generate_xlsx(self):
        common = Common()
        common.change_csv_to_xlsx(result_file, xlsx_file)

    def result_sort(self, result_list):
        # IP < OS < NIC
        ip_list = []
        ip_result = []
        os_list = []
        os_result = []
        nic_list = []
        nic_result = []

        for row_data in result_list:
            if row_data[0] not in ip_list:
                ip_list.append(row_data[0])
            if row_data[1] not in os_list:
                os_list.append(row_data[1])
            if row_data[2] not in nic_list:
                nic_list.append(row_data[2])

        ip_list.sort(reverse=False)
        os_list.sort(reverse=False)
        nic_list.sort(reverse=False)

        for ip_sort in ip_list:
            for row_data in result_list:
                if (ip_sort == row_data[0]) and (row_data not in ip_result):
                    ip_result.append(row_data)

        for os_sort in os_list:
            for row_data in ip_result:
                if (os_sort == row_data[1]) and (row_data not in os_result):
                    os_result.append(row_data)

        for nic_sort in nic_list:
            for row_data in os_result:
                if (nic_sort == row_data[2]) and (row_data not in nic_result):
                    nic_result.append(row_data)

        return nic_result


    def generate_env_state(self):
        head_data = ['IP', 'OS', 'NIC', 'Compiler', 'PASSED', 'FAILED', 'BLOCKED', 'Not Run', 'Grand Total']
        cur_result_list = []
        check_result_list = []
        cur_offset_data = ""
        result_list = []
        result_list_out = []
        common_fun = Common()

        latest_result = common_fun.get_csv_data(result_file)

        if latest_result is None:
            return
        for new_row in latest_result:
            single_result = []
            file_data = '{}{}{}{}'.format(new_row[0], new_row[1], new_row[2], new_row[3])
            if file_data == "osipnictarget":
                continue
            if cur_offset_data == file_data:
                continue
            else:
                # ip os nic tag
                single_result.append(new_row[1])
                single_result.append(new_row[0])
                single_result.append(new_row[2])
                single_result.append(new_row[3])
                cur_offset_data = file_data
            cur_result_list.append(single_result)

        for new_row in cur_result_list:
            if new_row not in check_result_list:
                check_result_list.append(new_row)

        for new_row in check_result_list:
            passed = 0
            failed = 0
            blocked = 0
            not_run = 0
            for last_row in latest_result:
                last_data = '{}{}{}{}'.format(last_row[0], last_row[1], last_row[2], last_row[3])
                check_data = '{}{}{}{}'.format(new_row[1], new_row[0], new_row[2], new_row[3])
                if last_data == check_data:
                    if last_row[6] == 'passed':
                        passed = passed + 1
                    elif last_row[6] == 'failed':
                        failed = failed + 1
                    elif last_row[6] == 'blocked':
                        blocked = blocked + 1
                    elif last_row[6] == 'Not Run':
                        not_run = not_run + 1

            tmp_result = []
            tmp_result.append(new_row[0])
            tmp_result.append(new_row[1])
            tmp_result.append(new_row[2])
            compiler = re.search('([a-z]*?)$', new_row[3]).group()
            tmp_result.append(compiler)
            tmp_result.append(passed)
            tmp_result.append(failed)
            tmp_result.append(blocked)
            tmp_result.append(not_run)
            total = passed + failed + blocked + not_run
            tmp_result.append(total)
            result_list.append(tmp_result)

        total_data = [0, 0, 0, 0, 0]
        for row_data in result_list:
            if row_data[0] == 'IP':
                continue
            else:
                for i in range(0, 5):
                    total_data[i] = total_data[i] + row_data[i + 4]

        total_result = []
        total_result.append('Grand Total')
        total_result.append(' N/A')
        total_result.append(' N/A')
        total_result.append(' N/A')
        for i in range(0, 5):
            total_result.append(total_data[i])

        result_list_out.append(head_data)
        result_list_out.append(total_result)

        # sort
        result_list = self.result_sort(result_list)
        result_list_out = result_list_out + result_list

        if os.path.exists(display_env_state):
            os.remove(display_env_state)
        common_fun.put_csv_data(display_env_state, result_list_out)
        common_fun.change_csv_to_xlsx(display_env_state, display_env_xlsx)

    def generate_suite_state(self):
        head_data = ['suite name']
        cur_result_list = []
        check_result_list = []
        cur_offset_data = ""
        result_list = []
        result_list_out = []
        suite_list = []
        common_fun = Common()
        result_column = 0
        data_list = [0, 0, 0, 0, 0, 0, 0]

        latest_result = common_fun.get_csv_data(result_file)

        if latest_result is None:
            return
        for new_row in latest_result:
            file_data = new_row[4]
            if file_data == 'suite name':
                for i in range(6, len(new_row)):
                    if i < (6 + 7):
                        head_data.append(new_row[i])
                    else:
                        break
                result_column = i - 5
                if result_column > 7:
                    result_column = 7
                continue

            if cur_offset_data == file_data:
                continue
            else:
                cur_result_list.append(file_data)
                cur_offset_data = file_data

        for new_row in cur_result_list:
            if new_row not in check_result_list:
                check_result_list.append(new_row)

        for new_row in check_result_list:
            for i in range(0, 7):
                data_list[i] = 0

            for last_row in latest_result:
                if new_row == last_row[4]:
                    for i in range(6, len(last_row)):
                        if i - 6 >= 7:
                            break
                        if last_row[i] == 'failed' or last_row[i] == 'blocked':
                            data_list[i - 6] = data_list[i - 6] + 1
            tmp_result = []
            tmp_result.append(new_row)
            for i in range(0, result_column):
                tmp_result.append(data_list[i])
            result_list.append(tmp_result)

        total_data = [0, 0, 0, 0, 0, 0, 0]
        for row_data in result_list:
            if row_data[0] == 'suite name':
                continue
            else:
                for i in range(0, result_column):
                    total_data[i] = total_data[i] + row_data[i + 1]

        total_result = ['Grand Total']
        for i in range(0, result_column):
            total_result.append(total_data[i])

        result_list_out.append(head_data)
        result_list_out.append(total_result)

        for row_data in result_list:
            if row_data[0] not in suite_list:
                suite_list.append(row_data[0])
        suite_list.sort(reverse=False)
        for ip_sort in suite_list:
            for row_data in result_list:
                if (ip_sort == row_data[0]) and (row_data not in result_list_out):
                    result_list_out.append(row_data)

        if os.path.exists(display_suite_state):
            os.remove(display_suite_state)
        common_fun.put_csv_data(display_suite_state, result_list_out)
        common_fun.change_csv_to_xlsx(display_suite_state, display_suite_xlsx)

    def generate_html(self):
        self.generate_env_state()
        self.generate_suite_state()

        if os.path.exists(display_env_html):
            os.remove(display_env_html)
        xd = pd.ExcelFile(display_env_xlsx)
        df = xd.parse()
        with codecs.open(display_env_html, 'w', 'utf-8') as html_file:
            html_file.write(df.to_html(header=True, index=False))

        if os.path.exists(display_suite_html):
            os.remove(display_suite_html)
        xd = pd.ExcelFile(display_suite_xlsx)
        df = xd.parse()
        with codecs.open(display_suite_html, 'w', 'utf-8') as html_file:
            html_file.write(df.to_html(header=True, index=False))

    def generate_report(self):
        self.generate_xlsx()
        self.generate_html()
