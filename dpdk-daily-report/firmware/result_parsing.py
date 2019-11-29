#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import re
# import datetime
import os
from common import Common
import xlrd
import shutil

latest_result_file = "./report/result.csv"
file_list_file = "./report/fail_list.csv"
file_case_list = []
result_txt_file = "./report/result.txt"
dts_log_file = "./report/dts.log"
dts_log_file_patch = '/var/www/DTS'


class ResultParsing(object):
    def __init__(self):
        print("Welcome to class ResultParsing")
        self.test_result_dir = ""
        self.test_time = ""
        self.test_nic = ""
        self.test_os = ""
        self.old_result = []
        self.new_result = []

    @staticmethod
    def generate_fail_list_file(file_case):
        head_data = ['os', 'ip', 'nic', 'target', 'suite name', 'case name', 'result']
        if file_case_list:
            file_case_list.append(file_case)
        else:
            file_case_list.append(head_data)
            file_case_list.append(file_case)

    def test_results_parsing(self, file_path, ower_data):
        result_file = file_path + '/test_results.json'
        xls_file = file_path + '/test_results.xls'
        target = 'N/A'
        ip = '0.0.0.0'
        ower_name = 'DPDK_CW'

        if os.path.exists(xls_file):
            if 0 == os.path.getsize(xls_file):
                print("file patch:{}.".format(file_path))
                return None
        else:
            return None
        xls_data = xlrd.open_workbook(xls_file)
        xls_sheet = xls_data.sheets()[0]
        nic_type = xls_sheet.row_values(1)
        self.test_nic = nic_type[2]

        if os.path.exists(result_file):
            pass
        else:
            return None

        with open(result_file) as f:
            data = f.readlines()
            lines = range(len(data))
            result = []
            for i in lines:
                if i == 1:
                    file_data = re.findall('"(.*?)"', data[i])
                    if file_data:
                        ip = file_data[0]
                elif i == 2:
                    file_data = re.findall('"(.*?)"', data[i])
                    if file_data:
                        target = file_data[0]
                else:
                    file_data = re.findall('"(.*?)"', data[i])
                    if file_data:
                        case_result = file_data[1]
                        file_data = file_data[0].split('/')
                        suite_name = file_data[0]
                        ower_name = ""
                        for j in range(len(ower_data)):
                            #print ower_data[j][0],ower_data[j][1]
                            #print ip
                            if ip == ower_data[j][0]:
                                ower_name = ower_data[j][1]
                                break
                            #else:
                            #    ower_name = ""
                        case_name = file_data[1]
                        result_date = []
                        result_date.append(self.test_os)
                        result_date.append(ip)
                        result_date.append(self.test_nic)
                        result_date.append(target)
                        result_date.append(suite_name)
                        result_date.append(case_name)
                        if case_result == 'n/a':
                            case_result = ' N/A'
                        result_date.append(case_result)
                        result_date.append(ower_name)
                        result.append(result_date)
                        if case_result == 'failed' or case_result == 'blocked':
                            self.generate_fail_list_file(result_date)
            f.close()
            return result

    def get_max_new_patch(self):
        base_dir = '/var/www/DPDK_TEST_RESULT'
        dir_list = os.listdir(base_dir)
        max_time = 0
        max_new_dir = ""
        for i in range(0, len(dir_list)):
            path = os.path.join(base_dir, dir_list[i])
            timestamp = os.path.getctime(path)
            if timestamp > max_time:
                max_time = timestamp
                max_new_dir = path
        self.test_result_dir = max_new_dir

        # print max_new_dir
        result_file_patch = max_new_dir + '/result.txt'
        if os.path.exists(result_file_patch):
            if os.path.exists(result_txt_file):
                os.remove(result_txt_file)
            shutil.copy(result_file_patch, result_txt_file)

        dst_file = dts_log_file_patch + '/dts.log'
        if os.path.exists(dst_file):
            if os.path.exists(dts_log_file):
                os.remove(dts_log_file)
            shutil.copy(dst_file, dts_log_file)

        # date = datetime.datetime.fromtimestamp(max_time) + datetime.timedelta(days=-1)
        # self.test_time = date.strftime('%Y-%m-%d')
        #import pdb
        #pdb.set_trace()
        path_layered = re.split('/', max_new_dir)
        time_layered = re.split('_', path_layered[4])
        self.test_time = time_layered[0]

    def generate_results_csv(self, ower_data):
        if not os.path.exists(self.test_result_dir):
            return
        cur_dir = self.test_result_dir
        dir_list = os.listdir(cur_dir)
        head_data = [['os', 'ip', 'nic', 'target', 'suite name', 'case name']]

        result_file = './output/{}_result.csv'.format(self.test_time)
        if os.path.exists(result_file):
            os.remove(result_file)

        common_fun = Common()

        for i in range(0, len(dir_list)):
            if os.path.isfile(dir_list[i]):
                continue
            path = os.path.join(cur_dir, dir_list[i])
            if os.path.isfile(path):
                continue
            test_os = re.findall('(.*?)_', dir_list[i])
            self.test_os = test_os[0]
            path_list = os.listdir(path)
            for j in range(0, len(path_list)):
                result_dir = os.path.join(path, path_list[j])
                write_data = self.test_results_parsing(result_dir, ower_data)
                if write_data is None:
                    continue
                if os.path.exists(result_file):
                    common_fun.put_csv_data(result_file, write_data)
                else:
                    date_time = self.test_time + '_result'
                    head_data[0].append(date_time)
                    head_data[0].append('ower')
                    common_fun.put_csv_data(result_file, head_data)
                    common_fun.put_csv_data(result_file, write_data)

        if os.path.exists(latest_result_file):
            os.remove(latest_result_file)
        shutil.copy(result_file, latest_result_file)

        if os.path.exists(file_list_file):
            os.remove(file_list_file)
        if file_case_list:
            common_fun.put_csv_data(file_list_file, file_case_list)
        else:
            common_fun.put_csv_data(file_list_file, head_data)

    def get_new_result(self, ower_data):
        # 获取最新一次测试结果路径
        self.get_max_new_patch()
        # 解析测试结果，生成csv文件
        self.generate_results_csv(ower_data)

    @staticmethod
    def get_old_result():
        old_file = './output/all_result.csv'

        if os.path.exists(old_file):
            common_fun = Common()
            date = common_fun.get_csv_data(old_file)
            return date
        else:
            old_file = './output/all_result.csv'
            head_data = [['os', 'ip', 'nic', 'target', 'suite name', 'case name']]
            common_fun = Common()
            common_fun.put_csv_data(old_file, head_data)
            date = common_fun.get_csv_data(old_file)
            return date

    def get_max_new_result(self):
        if self.test_time == "":
            self.get_max_new_patch()
        new_result_file = './output/{}_result.csv'.format(self.test_time)
        if os.path.exists(new_result_file):
            # print new_result_file
            pass
        else:
            return None
        common_fun = Common()
        date = common_fun.get_csv_data(new_result_file)
        return date

    def merge_all_result(self):
        self.old_result = self.get_old_result()
        self.new_result = self.get_max_new_result()
        all_result = []

        if self.new_result is None:
            return

        for old_row in self.old_result:
            found_flag = True
            new_result = []
            for new_row in self.new_result:
                str_old = '{}{}{}{}{}{}'.format(old_row[0], old_row[1], old_row[2], old_row[3], old_row[4], old_row[5])
                set_new = '{}{}{}{}{}{}'.format(new_row[0], new_row[1], new_row[2], new_row[3], new_row[4], new_row[5])
                if str_old == set_new:
                    for i in range(len(self.old_result[0])):
                        if len(old_row) - 1 >= i:
                            new_result.append(old_row[i])
                        if i == 5:
                            new_result.append(new_row[6])
                    all_result.append(new_result)
                    found_flag = False
                    continue
            if found_flag:
                for i in range(len(old_row)):
                    if i < 5:
                        new_result.append(old_row[i])
                    elif i == 5:
                        new_result.append(old_row[i])
                        new_result.append("Not Run")
                    else:
                        new_result.append(old_row[i])
                all_result.append(new_result)

        for new_row in self.new_result:
            found_flag = True
            new_result = []
            for old_row in self.old_result:
                str_old = '{}{}{}{}{}{}'.format(old_row[0], old_row[1], old_row[2], old_row[3], old_row[4], old_row[5])
                set_new = '{}{}{}{}{}{}'.format(new_row[0], new_row[1], new_row[2], new_row[3], new_row[4], new_row[5])
                if str_old == set_new:
                    found_flag = False
                    continue
            if found_flag:
                for i in range(len(self.old_result[0])):
                    if i < 5:
                        new_result.append(new_row[i])
                    elif i == 5:
                        new_result.append(new_row[i])
                        new_result.append(new_row[6])
                all_result.append(new_result)

        old_file = './output/all_result.csv'
        if os.path.exists(old_file):
            os.remove(old_file)
        common_fun = Common()
        common_fun.put_csv_data(old_file, all_result)
