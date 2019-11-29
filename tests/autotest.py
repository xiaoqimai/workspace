#!/usr/bin/python3

import paramiko
import re
import subprocess
import time
import os
import argparse

parser = argparse.ArgumentParser(description="auto test parameter")
parser.add_argument("-i", "--host_ip", help="dut ip")
parser.add_argument("-s", "--skip", action='store_true', help="skip dpdk build")
parser.add_argument("--output", help="specify log dir")
parser.add_argument("-v", "--verbose", help="show detail log on runtime")
parser.add_argument("-t", "--testcase", action="append", help="show detail log on runtime")
args = parser.parse_args()


class SSH_Con():

    def __init__(self, hostname, port=22, username="root", password="tester", timeout=15):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.get_conn()
        time.sleep(1)
        self.get_before()

    def get_conn(self):
        try:
            self.ssh.connect(self.hostname, self.port, self.username, self.password, timeout=self.timeout, allow_agent=False)
            self.chan = self.ssh.invoke_shell(width=10240, height=1024)
            return self.chan
        except Exception as e:
            print(e)
            raise Exception("connect to remote server %s failed" % self.hostname)

    def dis_conn(self):
        self.ssh.close()

    def get_before(self):
        if self.chan.recv_ready():
            out = self.chan.recv(102400).decode('utf-8')
            print("old info >>>\n%s" % out)

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
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
        out = p.communicate()
        if out[1]:
            return out[1].decode("utf-8")
        else:
            return out[0].decode("utf-8")

    def reboot_remote(self):
        try:
            print("reboot remote server %s ..." % self.hostname)
            self.send_expect('reboot', "# ", timeout=3)
            time.sleep(3)
            self.send_expect('whomai', expect="# ", timeout=3)
        except Exception as e:
            print(e)
            print("remote server %s has been restarted, wait for up..." % self.hostname)
            time.sleep(90)
            retry = 9
            while retry:
                if self.check_conn():
                    break
                else:
                    retry -= 1
                    time.sleep(30)
                    continue
            self.get_conn()
            self.send_expect("echo 0 > /proc/sys/kernel/randomize_va_space", "# ")

    def check_conn(self):
        cmd = "ping %s -w 5 -c 5" % self.hostname
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
        out = p.communicate()[0].decode("utf-8")
        print(out)
        if '64 bytes from' in out:
            return True
        else:
            return False

    def update_dts(self):
        print("check remote mount point...")
        path = '/mnt/nfs/DPDK_Builds/'
        if not os.path.exists(path):
            print("mounting resources...")
            self.exec_local("sshfs root@10.240.176.131:/var/www /mnt/nfs")
        print("update dts...")
        self.exec_local("rm -rf ./framework")
        self.exec_local("rm -rf ./tests")
        self.exec_local("rm -rf ./test_plans")
        self.exec_local("rm -rf ./executions")
        self.exec_local("rm -rf ./tools")
        self.exec_local("rm -rf ./nics")
        self.exec_local("rm -rf ./doc")
        self.exec_local("rm -rf ./dep")
        self.exec_local("rm -r ./dts")
        self.exec_local("rm -r ./dts.commit")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/framework  .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/tests  .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/test_plans .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/executions .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/tools .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/nics .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/dep .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/doc .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/dts .")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/conf/test_case_checklist.json ./conf/")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/conf/test_case_supportlist.json ./conf/")
        self.exec_local("cp -rf /mnt/nfs/DTS/dts/dts.log .")

        self.exec_local("mv dts.log dts.commit")
        print("update dpdk...")
        self.exec_local("rm -f ./dep/dpdk.tar.gz")
        self.exec_local("cp -f /mnt/nfs/DPDK/dpdk.tar.gz  ./dep")

    def run(self):
        os.chdir("/home/autoregression/cvl_test")
        print(self.exec_local('pwd'))
        #self.update_dts()
        self.reboot_remote()
        out_path = "jenkins_log/output_$(date '+%Y-%m-%d')"
        cmd = "mkdir -p %s" % out_path
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
        p.communicate()
        cmds = ['./dts']
        if args.skip:
            cmds.append('-s')
        if args.output:
            cmds.append('--output ' + args.output)
        else:
            cmds.append("--output jenkins_log/output_$(date '+%Y-%m-%d')")
        cmd = " ".join(cmds)
        cmd = cmd + " 2>&1 |tee -a jenkins_log/$(date '+%Y-%m-%d').log"
        print("execute command: %s" % cmd)
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
            while True:
                out = p.stdout.readline().decode('utf-8')
                print(out)
                if 'DTS ended' in out:
                    p.kill()
                    break
        except Exception as e:
            print(e)
            



if __name__ == '__main__':
    print(args.host_ip)
    ssh = SSH_Con(args.host_ip)
    ssh.run()
    ssh.reboot_remote()
    ssh.dis_conn()








