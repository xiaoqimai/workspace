#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# @Time  : ${DATE} ${TIME}
# @File  : ${NAME}.py
# @email : box.c.chen@intel.com
__author__ = 'Chen Bo'

import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

display_env_html = "./report/env_state.html"
display_suite_html = "./report/suite_state.html"
display_result_txt = "./report/result.txt"
display_dts_log = "./report/dts.log"

file_list_file = "./report/fail_list.csv"
latest_result_file = "./report/result.csv"
all_result_file = "./report/all_result.xlsx"


class SendMail(object):
    def __init__(self):
        print("Welcome to class SendMail")

    def add_css(self, content):
        content = content.replace("text-align: right;", "text-align: right; background:lightblue")
        content = content.replace('table border="1" class="dataframe"',
                                  'table border="1px" class="dataframe" style="margin-left:33.75pt"')
        content = content.replace("""<tr><td>Grand Total</td>""",
                                  """<tr style='background:lightblue'><td>Grand Total</td>""")
        content = content.replace("""<tr><td>Gobal total</td>""",
                                  """<tr style='background:lightblue'><td>Grand Total</td>""")
        new_content = "<style>td{text-align:left;font-family:Calibri;font-size:11.0pt;} th{text-align:center;font-family:Calibri} </style>" + content
        p = re.compile(r"<td>\d{0,4}</td>")
        list_data = re.findall(p, new_content)
        for i in list_data:
            b = str(re.findall('\d{1,4}', i))
            if len(b) == 0:
                b = ""
            else:
                b = b[2:-2]
            c = re.sub(i, '<td style="text-align: right;">%s</td>' % b, new_content)
            new_content = c
        return new_content

    def read_dts(self):
        path = display_dts_log
        with open(path, 'r') as f:
            txt = f.readlines()
        f.close()
        dts_commit = re.findall(r'commit (.*)', txt[0])[0]
        dts_Author = re.findall(r'Author: (.*)', txt[1])[0]
        dts_date = re.findall(r'Date:   (.*)', txt[2])[0]
        dts_comment = txt[4].strip('  ').strip('\n')
        return dts_commit, dts_Author, dts_date, dts_comment

    def read_txt(self):
        file_name = display_result_txt
        with open(file_name, 'r') as f:
            txt = f.readlines()
        f.close()
        value1 = txt[4].strip("\n")
        key2_value2 = txt[7].strip("\n")
        key3_value3 = txt[9].strip("\n")
        key4_value4 = txt[11].strip("\n")
        key5_value5 = txt[13].strip("\n")
        TEST_PATH = value1
        dpdk_commit = key2_value2.split("|")[-1].strip()
        auther_email = key3_value3.split("|")[-1].strip().replace("<", "&lt;").replace(">", "&gt")
        now_Date = key4_value4.split("|")[-1].strip()
        dpdk_version = key5_value5.split("|")[-1].strip()
        content = """<style> p {margin:0;margin-left:.5in;font-family:Calibri;font-size: 11.0pt;color:#1F497D;}</style><p>Test Result Path:<a href="file:///%s">%s</a></p><p style='margin-left:.75in'><u>DPDK commit</u>: %s</p><p style='margin-left:.75in'><u>DPDK Author</u>: %s</p><p style='margin-left:.75in'><u>DPDK Date</u>: %s</p><p style='margin-left:.75in'><u>DPDK Comment</u>: %s</p>""" % (
            TEST_PATH, TEST_PATH, dpdk_commit, auther_email, now_Date, dpdk_version)
        dts_commit, dts_Author, dts_date, dts_comment = self.read_dts()
        dts_Author = dts_Author.replace("<", "&lt;").replace(">", "&gt")
        dts_content = """<p style='margin-left:.75in'><u>DTS commit</u>: %s</p><p style='margin-left:.75in'><u>DTS Author</u>: %s</p><p style='margin-left:.75in'><u>DTS Date</u>: %s</p><p style='margin-left:.75in'><u>DTS Comment</u>: %s</p>""" % (
            dts_commit, dts_Author, dts_date, dts_comment)

        content = content + dts_content
        content = content.replace("<p style='margin-left:.75in'><u>DTS commit",
                                  "<p>DTS:</p><p style='margin-left:.75in'><u>DTS commit")
        content = content.replace("<p style='margin-left:.75in'><u>DPDK commit",
                                  "<p>DPDK:</p><p style='margin-left:.75in'><u>DPDK commit")
        return content

    def send_report(self, _from, _to, _sub, _cc, _content):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = _sub
        msg['From'] = _from
        msg['CC'] = ",".join(_cc)
        msg['To'] = ", ".join(_to)
        part2 = MIMEText(_content, "html", "utf-8")
        msg.attach(part2)

        att1 = MIMEText(open(file_list_file, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        att1["Content-Disposition"] = 'attachment; filename="fail_list.csv"'
        msg.attach(att1)
        att2 = MIMEText(open(latest_result_file, 'rb').read(), 'base64', 'utf-8')
        att2["Content-Type"] = 'application/octet-stream'
        att2["Content-Type"] = 'application/octet-stream'
        att2["Content-Disposition"] = 'attachment; filename="result.csv"'
        msg.attach(att2)
        att3 = MIMEText(open(all_result_file, 'rb').read(), 'base64', 'utf-8')
        att3["Content-Type"] = 'application/octet-stream'
        att3["Content-Type"] = 'application/octet-stream'
        att3["Content-Disposition"] = 'attachment; filename="all_result.xlsx"'
        msg.attach(att3)

        """
        att4 = MIMEText(open('/home/failed_rate_20/month.xlsx', 'rb').read(), 'base64', 'utf-8')
        att4["Content-Type"] = 'application/octet-stream'
        att4["Content-Type"] = 'application/octet-stream'
        att4["Content-Disposition"] = 'attachment; filename="daily_result.xlsx"'
        msg.attach(att4)
        """

        smtp_service = smtplib.SMTP('smtp.intel.com')
        smtp_service.sendmail(_from, _to, msg.as_string())
        smtp_service.quit()
        print "Send complete"

    def send_report_intel(self, _from, _to, _sub, _cc, _content):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = _sub
        msg['From'] = _from
        msg['CC'] = ",".join(_cc)
        msg['To'] = ", ".join(_to)
        part2 = MIMEText(_content, "html", "utf-8")
        msg.attach(part2)

        smtp_service = smtplib.SMTP('smtp.intel.com')
        smtp_service.sendmail(_from, _to, msg.as_string())
        smtp_service.quit()
        print "Send intel complete"

    def result_send(self):
        from_maillist = "sys_stv@intel.com"
        rece_maillist = ["npg-prc-sw.stv.dpdk@intel.com", "dpdk_cw@intel.com", "box.c.chen@intel.com"]
        rece_maillist.append("junx.w.zhou@intel.com")
        rece_maillist.append("qimaix.xiao@intel.com")
        rece_maillist.append("xiaoxiaox.zeng@intel.com")
        rece_maillist.append("weix.xie@intel.com")
        rece_maillist.append("xix.zhang@intel.com")
        rece_maillist_intel = ["npg-prc-sw.stv.dpdk@intel.com", "dpdk_cw@intel.com", "ferruh.yigit@intel.com", "cathal.ohare@intel.com"]
        #rece_maillist = ["box.c.chen@intel.com"]
        #rece_maillist_intel = ["box.c.chen@intel.com"]
        subject = "[test-report-part]DPDK Regression Test Report Internal Use"
        subject_intel = "[test-report-part]DPDK Regression Test Report"
        cc_maillist = []
        if os.path.exists(display_env_html):
            file_html = open(display_env_html, "rb")
            content = file_html.read()
            new_content1 = self.add_css(content)
        else:
            print('Error:Not found {}'.format(display_env_html))
            return

        if os.path.exists(display_env_html):
            file_html2 = open(display_suite_html, "rb")
            content = file_html2.read()
            new_content2 = self.add_css(content)
        else:
            print('Error:Not found {}'.format(display_suite_html))
            file_html.close()
            return

        h1 = """<br/><br/><strong style="font-family:Calibri;background:aqua;">         Failed test suite daily track(failed rate >=10%): </strong><br/><br/>"""
        h2 = """<br/><strong style="font-family:Calibri;background:aqua;">      Test suites by platform: </strong><br/>"""
        h0 = """<strong style="font-family:Calibri;background:aqua;">           Summary： </strong><br/>"""

        content0 = self.read_txt()

        content = h0 + content0 + h2 + new_content1 + h1 + new_content2
        content = "<style>td{text-align:left;font-family:Calibri} th{text-align:center;font-family:Calibri} </style>" + content
        content = content.replace('td style="', 'td style="font-family: Calibri;font-size:11.0pt;')
        content = content.replace("<td>", "<td style='font-family: Calibri;font-size: 11.0pt;'>")
        self.send_report(from_maillist, rece_maillist, subject, cc_maillist, content)
        self.send_report_intel(from_maillist, rece_maillist_intel, subject_intel, cc_maillist, content)
