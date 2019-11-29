#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

"""
#解析配置文件
#解析最新的测试结果
#合并测试结果
#生成测试报告
#数据结果校验
#发送邮件
"""

from configure_file_parsing import ConfigureFileParsing
from result_parsing import ResultParsing
from report import GenerateReport
from send_mail import SendMail


class DailyReport(object):
    def __init__(self):
        print("Welcome to class DailyReport")

        """
        ['suite1', 'ower1'],
        ['suite2', 'ower2'],
        ['suite3', 'ower3']
        """
        self.ower_data = []

    def get_daily_report(self):
        # 解析配置文件
        #ower_list = ConfigureFileParsing()
        #self.ower_data = ower_list.get_suite_ower()
        # 解析最新的测试结果
        #new_result = ResultParsing()
        #new_result.get_new_result(self.ower_data)
        # 合并测试结果
        #new_result.merge_all_result()
        # 生成测试报告
        #report = GenerateReport()
        #report.generate_report()
        # 数据结果校验--暂未实现
        # 发送邮件
        mail = SendMail()
        mail.result_send()
