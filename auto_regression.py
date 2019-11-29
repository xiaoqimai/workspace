#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2019/10/12
# @Author  : DPDK CW
# @File    : auto_regression.py
#
# CI jenkins script

try:
    import pxssh
except ImportError:
    from pexpect import pxssh

import os
import argparse
import subprocess
import time

parser = argparse.ArgumentParser(description="dpdk regression test")
parser.add_argument("-d", "--destdir", help="save test result")
parser.add_argument("-o ", "--os", help="set up os type")
parser.add_argument("-n ", "--nic", help="set up nic type")
parser.add_argument("-t ", "--testtype", help="set up test type")
parser.add_argument("-i ", "--ip", help="set up tester ip")
parser.add_argument("-p", "--patch", action="store_true", help="for patch test")
parser.add_argument("-m", "--mail", action="store_true", help="for mail test")

parser.add_argument("-T", "--targets", action="append",
                    help="for target test with execution conf file, the format should be target,conf")
parser.add_argument("-R", "--reboot", action="store_true", help="reboot the dut device")
parser.add_argument("-comm ", "--dts_commit", action="store_true", help="set up the boolean value  for dts_commmit")
parser.add_argument("-rerun", "--rerun", help="rerun the failed cases")
args = parser.parse_args()


class Schedule(object):
    def __init__(self, host, username, passwd):
        self.ub_order = 0
        self.rhel_order = 4
        self.fed_order = 5
        self.hostname = host
        self.username = username
        self.password = passwd
        self.dest_dir = args.os + "_" + args.nic + "_" + args.testtype
        self.conf_file = ''

    def set_up_all(self):
        cmd = "sed -i 's/10.240.176.131/10.240.176.131/g' /etc/fstab"
        self.execute_local(cmd)
        if os.path.exists("/root/.ssh/known_hosts"):
            os.remove("/root/.ssh/known_hosts")

        if not os.path.exists("/mnt/nfs/DPDK_Builds"):
            self.execute_local("mount -t nfs 10.240.176.131:/var/www /mnt/nfs")

        if args.destdir is None:
            args.destdir = self.execute_local("sed -n '1 p' /mnt/nfs/DPDK/buildnum").split("\n")[0]

    @staticmethod
    def check_os_conn():
        p = subprocess.Popen(["ping -w 5 -c 5 " + args.ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                             cwd=os.getcwd())
        out = p.communicate()[0]
        print out
        if "64 bytes from " in out:
            return True
        else:
            return False

    def obtain_session(self):
        session = pxssh.pxssh()
        session.login(self.hostname, self.username, self.password)
        return session

    def restart_dut(self):
        if args.reboot:
            session = self.obtain_session()
            try:
                session.sendline("reboot")
                session.prompt()
            except pxssh.ExceptionPxssh, e:
                print str(e)
                print "DUT have been restarted"
            print "Waiting for [DUT]" + args.ip + " ..."
            time.sleep(360)
            if args.os == "FreeBSD10" and args.nic == "Fortville_spirit":
                session = self.obtain_session()
                session.sendline("kldload nic_uio.ko")
                session.prompt()
                session.sendline("kldload contigmem.ko")
                session.prompt()
            # Disable ASLR
            session = self.obtain_session()
            session.sendline("echo 0 > /proc/sys/kernel/randomize_va_space")
            session.prompt()

    def prepare_pkg(self):
        print "<<<prepare dpdk source code>>>"
        # if args.patch:
        #     self.execute_local("rm -f ./dep/dpdk.tar.gz")
        #     self.execute_local("cp -f /mnt/nfs/DPDK/temp_pkg/dpdk.tar.gz  ./dep")
        #
        # else:
        #     self.execute_local("rm -f ./dep/dpdk.tar.gz")
        # self.execute_local("cp -f /mnt/nfs/DPDK/dpdk.tar.gz  ./dep")

    def run(self):
        self.set_up_all()
        self.update_dts()
        self.prepare_pkg()
        self.get_dut_config()
        self.restart_dut()
        if args.targets is not None:
            for target_conf in args.targets:
                print "target_conf=%s target_conf type is %s" % (target_conf, str(type(target_conf)))
                m = target_conf.split(',')
                print "m=%s " % str(m)
                target = m[0].rstrip()
                if len(m) == 2:
                    self.conf_file = m[1].rstrip()
                else:
                    self.conf_file = 'execution.cfg'
                if self.check_os_conn():
                    self.clean_up_log()
                    print "<< executing " + target + " >>"
                    start = self.execute_local(
                        "sed -n '/targets/=' %s | awk '{if (NR ==1) print $1 }'" % self.conf_file).split("\n")[0]
                    print "start is %s" % start
                    print self.conf_file
                    end = self.execute_local(
                        "sed -n '/para/=' %s | awk '{if (NR ==1) print $1 }'" % self.conf_file).split("\n")[0]
                    cmd = "sed -i '" + (
                        str(int(start) + 1)) + "," + (str(int(end) - 1)) + "c\    " + target + "' " + self.conf_file
                    self.execute_local(cmd)
                    try:
                        if args.rerun is None:
                            p = subprocess.Popen(["`pwd`/dts --config-file %s 2>&1 |tee -a %s_%s.log" % (
                                self.conf_file, self.dest_dir, target)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                 shell=True, cwd=os.getcwd())
                        else:
                            p = subprocess.Popen(["`pwd`/dts --re_run %s --config-file %s 2>&1 |tee -a %s_%s.log" % (
                                args.rerun, self.conf_file, self.dest_dir, target)], stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
                        for line in iter(p.stdout.readline, ''):
                            print line
                            if 'DTS ended' in line:
                                p.kill()
                    except Exception, e:
                        print e
                    self.backup_log(target)
                    print "<< Finished " + target + " >>"
                    self.restart_dut()
                else:
                    print "[DUT:]" + args.ip + " restarted ,but cannot get the connection ,please check!"
                    break
        else:
            self.conf_file = 'execution.cfg'
            if self.check_os_conn():
                self.clean_up_log()
                try:
                    out = os.popen("`pwd`/dts 2>&1 |tee -a " + self.dest_dir + ".log")
                    for line in iter(out.readline, ''):
                        print line
                        out.flush()
                except Exception, e:
                    print e
                    print "terminated!backup log..."
                self.backup_log()
            else:
                print "[DUT:]" + args.ip + " restarted ,but cannot get the connection ,please check!"

    def update_dts(self):
        print "<<<update dts code>>>"

        self.execute_local("rm -rf ./framework")
        self.execute_local("rm -rf ./tests")
        self.execute_local("rm -rf ./test_plans")
        self.execute_local("rm -rf ./executions")
        self.execute_local("rm -rf ./tools")
        self.execute_local("rm -rf ./nics")
        self.execute_local("rm -rf ./doc")
        self.execute_local("rm -rf ./dep")
        self.execute_local("rm -r ./dts")
        self.execute_local("rm -r ./dts.commit")

        if not args.dts_commit:
            dts_commit = "5860f677c2273a1a51f74c1b9e5d52afb045968aModifyScpPatch"
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/framework  .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/tests  .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/test_plans .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/executions .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/tools .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/nics .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/dep .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/doc .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/dts .")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/conf/dpdk_test_case_checklist.xls ./conf/")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/conf/dpdk_support_test_case.xls ./conf/")
            self.execute_local("cp -rf /mnt/nfs/DTS/" + dts_commit + "/dts/dts.log .")
        else:
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/framework  .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/tests  .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/test_plans .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/executions .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/tools .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/nics .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/dep .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/doc .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/dts .")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/conf/test_case_checklist.json ./conf/")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/conf/test_case_supportlist.json ./conf/")
            self.execute_local("cp -rf /mnt/nfs/DTS/dts/dts.log .")

        self.execute_local("mv dts.log dts.commit")
        # self.execute_local("patch -p1 < 0001-vlan-add-time.patch")

    @staticmethod
    def execute_local(cmd):
        print cmd
        out_stream = os.popen(cmd)
        out = out_stream.read()
        out_stream.close()
        print out
        return out

    def get_dut_config(self):
        config = []
        session = self.obtain_session()
        session.sendline("uname -r")
        session.prompt()
        kernel_info = session.before.split("\r\n", 1)[1]
        config.append("Kernel Version:" + kernel_info + "\n")
        if "FreeBSD" in args.os:
            session.sendline("grep -i CPU: /var/run/dmesg.boot")
            session.prompt()
            cpu_info = session.before.split("\r\n", 1)[1]
            config.append("CPU info:" + cpu_info + "\n")
            session.sendline("gcc48 -v")
            session.prompt()
            gcc_info = session.before.rsplit("\r\n", 2)[1]
            config.append("GCC Version:" + gcc_info + "\n")
        else:
            session.sendline("cat /proc/cpuinfo |grep 'model name'|uniq|awk -F: '{print $2}'")
            session.prompt()
            cpu_info = session.before.split("\r\n", 1)[1]
            config.append("CPU info:" + cpu_info + "\n")
            session.sendline("gcc -v")
            session.prompt()
            gcc_info = session.before.rsplit("\r\n", 2)[1]
            config.append("GCC Version:" + gcc_info + "\n")
        with open("system.conf", "wb") as code:
            code.write(str(config))
        print config

    def backup_log(self, target=None):
        print "<<<backup test results>>>"

        self.execute_local("cp -f `pwd`/%s `pwd`/output" % self.conf_file)
        self.execute_local("cp -f `pwd`/system.conf `pwd`/output")
        self.execute_local("cp -f `pwd`/system.conf `pwd`/output")
        print(args.destdir)
        print(self.dest_dir)

        if target is not None:
            self.execute_local("cp -f " + self.dest_dir + "_" + target + ".log" + " output")
            self.execute_local(
                "zip -r -P dts_test output.zip output  2>&1 |tee -a " + self.dest_dir + "_" + target + ".log")
            self.execute_local("mkdir -p " + args.destdir + "/" + self.dest_dir + "/" + target)
            self.execute_local("rm -rf  " + args.destdir + "/" + self.dest_dir + "/" + target + "/*")
            self.execute_local("cp -rf output/* " + args.destdir + "/" + self.dest_dir + "/" + target + "/")
        else:
            self.execute_local("cp -f " + self.dest_dir + ".log" + " output")
            self.execute_local("zip -r -P dts_test output.zip output  2>&1 |tee -a " + self.dest_dir + ".log")
            self.execute_local("mkdir -p " + args.destdir + "/" + self.dest_dir)
            self.execute_local("rm -rf  " + args.destdir + "/" + self.dest_dir + "/*")
            self.execute_local("cp -rf output/* " + args.destdir + "/" + self.dest_dir + "/")

        if not os.path.exists(args.destdir + "/" + "dpdk.tar.gz"):
            self.execute_local("cp -f `pwd`/dep/dpdk.tar.gz {}".format(args.destdir))

    def clean_up_log(self):
        print "<<<cleanup test results>>>"
        self.execute_local("rm -rf output*")
        self.execute_local("rm -rf *.log")


if __name__ == "__main__":
    schedule = Schedule(args.ip, 'root', 'tester')
    if schedule.check_os_conn():
        schedule.run()
    else:
        print "Connection Error,please check the connection of the [DUT:]" + args.ip

