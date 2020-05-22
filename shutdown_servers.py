#!/usr/bin/python3

import paramiko
import re
import subprocess
import time
import os
import threading
import json


class SSH():

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
        self.ssh.connect(self.hostname, self.port, self.username, self.password, timeout=self.timeout)
        self.chan = self.ssh.invoke_shell(width=1024, height=1024)
        return self.chan

    def dis_conn(self):
        self.ssh.close()

    def get_before(self):
        if self.chan.recv_ready():
            out = self.chan.recv(102400).decode('utf-8')
            # print("old info >>>\n%s" % out)

    def send_command(self, cmd, buff=102400, timeout=3):
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

    def send_expect(self, cmd, expect, buff=102400, timeout=15):
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

    def check_remote(self):
        try:
            out = self.send_expect('uname -a', "# ", timeout=5)
            print(out)
            out2 = self.send_expect('whoami', expect="# ", timeout=3)
            print(out2)
        except Exception as e:
            print(e)

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

def get_alive_ip_addrs(subnet="10.240.183.", count=2):
    ip_addrs = []
    for i in range(254):
        addr = subnet+str(i+2)
        cmd = "ping %s -n %s -w 1" % (addr, count) if os.name == 'nt' else "ping %s -W 1 -c %s" % (addr, count)
        out = SSH.exec_local(cmd)
        if not ("100% packet loss" in out or "100% loss" in out):
            ip_addrs.append(addr)
    shutdown_servers = len(ip_addrs)
    print("total %d servers to be shutdown" % shutdown_servers)
    return ip_addrs

lock = threading.Lock()
f = open("shutdown.log", "a+")
def shutdown(ip):
    try:
        ssh = SSH(hostname=ip)
    except Exception as e:
        print(e)
        result = "ssh to %s, failed." % ip
    else:
        result = ssh.shutdown_remote()
        lock.acquire()
        f.write("%s: %s"%(ip, result))
        f.flush()
        lock.release()
    print({ip: result})

def main():
    ip_addrs = get_alive_ip_addrs()
    ths = []
    for i in ip_addrs:
        t = threading.Thread(target=shutdown, args=(i,), name=i)
        ths.append(t)
    for t in ths:
        t.start()
        print("%s is shuting down..." % t.name)
        t.join()
    f.close()
    print("shutdown server finished")

if __name__ == '__main__':
    main()
    # ip_addrs = get_alive_ip_addrs()
    # print(ip_addrs)
    # ssh = SSH(hostname=ip_addrs[0])
    # ssh.check_remote()










