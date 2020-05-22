#!/usr/bin/python3

import paramiko
import re
import subprocess
import time
import os
import threading
import json
import xlrd
import xlwt
import datetime
from copy import deepcopy

lock = threading.Lock()
today = datetime.datetime.today()
day_str = time.strftime("%Y-%m-%d")
log_file = "fdisk_scan_%s.log" % day_str
check_ip = None
if os.path.exists(log_file):
    with open(log_file,"r") as f:
        check_ip = json.load(open(log_file, "r")).get("check_ip")
results = [["server ip", "connect status", "total disk", "disk sn"]]


class SSH(object):

    def __init__(self, hostname, username="root", port=22, password="tester", timeout=15):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.ssh = paramiko.SSHClient()
        self.get_conn()
        time.sleep(1)
        self.get_before()

    def get_conn(self):
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.hostname == '10.240.183.131':
            self.ssh.connect(self.hostname, self.port, self.username, 'tester123!', timeout=self.timeout)
        else:
            self.ssh.connect(self.hostname, self.port, self.username, self.password, timeout=self.timeout)
        self.chan = self.ssh.invoke_shell(width=1024, height=1024)
        return self.chan

    def dis_conn(self):
        self.ssh.close()

    def get_before(self):
        if self.chan.recv_ready():
            out = self.chan.recv(102400).decode('utf-8')
            # print("old info >>>\n%s" % out)

    def send_command(self, cmd, buff=1024000, timeout=3):
        self.get_before()
        end_time = time.time() + timeout
        if self.chan.send_ready():
            self.chan.send(cmd + '\n')
            time.sleep(0.2)
            out = ''
            while end_time - time.time()>=0:
                if self.chan.recv_ready():
                    tmp = self.chan.recv(buff).decode('utf-8')
                    out += tmp
                if out.endswith(('$ ', '# ')) and not self.chan.recv_ready():
                    return out
                time.sleep(0.2)
            return out

    def send_expect(self, cmd, expect, buff=1024000, timeout=15):
        self.get_before()
        end_time = time.time() + timeout
        if self.chan.send_ready():
            self.chan.send(cmd + '\n')
            out = ''
            while end_time - time.time() >= 0:
                if self.chan.recv_ready():
                    tmp = self.chan.recv(buff).decode("utf-8")
                    out += tmp
                    p = re.compile(expect)
                    m = p.search(out)
                    if m:
                        return out
            else:
                print("TIMEOUT: OUTPUT IS:\n %s" % out)
                raise Exception("TIMEOUT Error")

    @staticmethod
    def exec_local(cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out = p.communicate(timeout=10)
        if out[1]:
            return out[1].decode("utf8")
        else:
            return out[0].decode("utf8")

    def shutdown_remote(self):
        try:
            self.send_expect('shutdown now', "# ", timeout=5)
            time.sleep(5)
            self.send_expect('whoami', expect="# ", timeout=3)
        except Exception as e:
            print(e)
            print("remote server %s has been shutdown..." % self.hostname)
            return True
        else:
            return self.check_conn()

    def scan_disk_li(self):
        out = self.send_command('fdisk -l', timeout=1)
        p = re.compile('Disk\s+(/dev/sd.+?):')
        disk_info = p.findall(out)
        return disk_info

    def get_ostype(self):
        out = self.send_expect("cat /etc/os-release", "# ", timeout=1)
        m = re.search('NAME=(.+?)\s', out)
        if m:
            os_type = m.group(1)
        else:
            os_type = None
            print("get os type failed")
        return os_type

    def install_hdparm(self):
        os_type = self.get_ostype()
        if "Red Hat" in os_type or "CentOS" in os_type or "Fedora" in os_type:
            installer = "yum"
        elif "Ubuntu" in os_type:
            installer = "apt"
        elif "SLES" in os_type:
            installer = "zypper"
        else:
            installer = None

        cmd = "%s -y install hdparm" % installer if installer else ''
        self.send_expect(cmd, "# ", timeout=60)

    def scan_disk_sn(self, f_list=None):
        f_list = "/dev/sda" if not f_list else f_list
        p = re.compile('SerialNo=(.+?)\s')
        sns = []
        if isinstance(f_list, list):
            for i in f_list:
                try:
                    print("%s is scanning..." % self.hostname)
                    out = self.send_expect('hdparm -i %s' % i, "# ", timeout=2)
                    if "command not found" in out:
                        self.install_hdparm()
                        out = self.send_expect('hdparm -i %s' % i, "# ", timeout=2)
                    m = p.search(out)
                    if m:
                        sns.append(m.group(1))
                    else:
                        sns.append("Invalid_SN")
                except Exception as e:
                    print(e)
                    sns.append("no_hdparm")
        else:
            try:
                out = self.send_expect('hdparm -i %s' % f_list, "# ", timeout=2)
                if "command not found" in out:
                    self.install_hdparm()
                    out = self.send_expect('hdparm -i %s' % f_list, "# ", timeout=2)
                m = p.search(out)
                if m:
                    sns.append(m.group(1))
                else:
                    sns.append("Invalid_SN")
            except Exception as e:
                print(e)
                sns.append("no_hdparm")
        sns = list(set(sns))
        print(sns)
        return sns

    def check_conn(self):
        cmd = "ping %s -w 5 -n 5" % self.hostname if os.name=='nt' else "ping %s -w 5 -c 5" % self.hostname
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
        out = p.communicate()[0].decode("utf8")
        print(out)
        if "timed out" in out or "100% packet loss" in out:
            return True
        else:
            print("server %s not shutdown success in 10s" % (self.hostname))
            return True

# def get_alive_ip_addrs(subnet="10.240.183.", count=1):
#     ip_addrs = []
#     for i in range(254):
#         addr = subnet+str(i+2)
#         cmd = "ping %s -n %s -w 1" % (addr, count) if os.name == 'nt' else "ping %s -W 1 -c %s" % (addr, count)
#         out = SSH.exec_local(cmd)
#         if not ("100% packet loss" in out or "100% loss" in out):
#             ip_addrs.append(addr)
#         else:
#             print("%s not in connection" % addr)
#     print(ip_addrs)
#     scan_servers = len(ip_addrs)
#     print("total %d servers to scan" % scan_servers)
#     with open("ip_list.txt", "w") as f:
#         f.write('\n'.join(ip_addrs))
#     return ip_addrs

ip_addrs = []
def get_ips(addr, count):
    cmd = "ping %s -n %s -w 1" % (addr, count) if os.name == 'nt' else "ping %s -W 1 -c %s" % (addr, count)
    out = SSH.exec_local(cmd)
    if not ("100% packet loss" in out or "100% loss" in out):
        lock.acquire()
        ip_addrs.append(addr)
        lock.release()
    else:
        print("%s not in connection" % addr)

def get_ip_fast(subnet='10.240.183.'):
    ths = []
    for i in range(254):
        addr = subnet+str(i+2)
        t = threading.Thread(target=get_ips, args=(addr,2), name=addr)
        t.start()
        ths.append(t)
    for j in ths:
        j.join()
    scan_servers = len(ip_addrs)
    print("total %d servers to scan" % scan_servers)
    if scan_servers > 0:
        with open("ip_list_%s.txt" % day_str, "w") as f:
            f.write('\n'.join(ip_addrs))
    return ip_addrs


def save_results(results):
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet(day_str, cell_overwrite_ok=True)
    for i in range(len(results)):
        for j in range(len(results[i])):
            sheet.write(i, j, results[i][j])
    wbk2 = deepcopy(wbk)
    wbk2.save("check_sn_result.xls")

def scan_disks(ip):
    try:
        ssh = SSH(hostname=ip)
    except Exception as e:
        print("ssh to %s, failed." % ip)
        results.append([ip, False, "unknown", "unknown"])
        print([ip, False, "unknown", "unknown"])
    else:
        disk_li = ssh.scan_disk_li()
        disk_sn = ssh.scan_disk_sn(disk_li)
        lock.acquire()
        results.append([ip, True, len(disk_sn), ', '.join(disk_sn)])
        lock.release()
        print([ip, True, len(disk_sn), disk_sn])

def main():
    ip_addrs = check_ip if check_ip else get_ip_fast()
    ths = []
    for i in ip_addrs:
        t = threading.Thread(target=scan_disks, args=(i,), name=i)
        ths.append(t)
    for t in ths:
        t.start()
        t.join()
    save_results(results)
    with open(log_file, "w") as f:
        json.dump({"check_ip": ip_addrs}, f)
    print("servers scan finished")

if __name__ == '__main__':
    main()










