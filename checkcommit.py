#!/usr/bin/python3

import paramiko
import os
import re
import json
import argparse
import time


class Conn(object):
    def __init__(self, hostname, uesrname='root', password='tester', port=22, timeout=300):
        self.hostname = hostname
        self.username = uesrname
        self.passwork = password
        self.port = port
        self.timeout = timeout
        self.ssh = None
        self.chan = None
        self.get_connect()

    def get_connect(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print("connecting to %s..." % self.hostname)
            self.ssh.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.passwork,
                             allow_agent=False, look_for_keys=False, timeout=self.timeout)
            self.chan = self.ssh.invoke_shell(width=1024, height=1024)
            time.sleep(0.5)
        except Exception as e:
            print("failed to connect to %s" % self.hostname)
            raise Exception(e)

    def send_cmd(self, cmd, buffsize=102400, timeout=15):
        if self.chan.recv_ready():
            self.chan.recv(buffsize).decode()
        while True:
            t0 = time.time()
            if self.chan.send_ready():
                self.chan.sendall(cmd + '\n')
                output = ''
                while time.time() - t0 < timeout:
                    time.sleep(0.5)
                    if self.chan.recv_ready():
                        tmp = self.chan.recv(buffsize).decode()
                        print(tmp)
                        output += tmp
                    time.sleep(0.1)
                return output
            elif time.time() - t0 < timeout:
                print("session not ready for send")
                continue
            else:
                raise Exception("send command %s failed" % cmd)

    def send_expect(self, cmd, expect, buffsize=102400, timeout=15):
        if self.chan.recv_ready():
            self.chan.recv(buffsize).decode()
        while True:
            t0 = time.time()
            if self.chan.send_ready():
                self.chan.sendall(cmd + '\n')
                output = ''
                while time.time() - t0 < timeout:
                    time.sleep(0.5)
                    if self.chan.recv_ready():
                        tmp = self.chan.recv(buffsize).decode()
                        print(tmp)
                        tmp_output = output.splitlines()[-1] + tmp if output else tmp
                        output += tmp
                        if expect in tmp_output:
                            return output[:output.find(expect)]
                    time.sleep(0.5)
                else:
                    raise Exception("TMOUT for expect %s\nOUTPUT: %s" % (expect, output))
            elif time.time() - t0 < timeout:
                print("session not ready for send")
                continue
            else:
                raise Exception("send command %s failed" % cmd)


class CheckCommit(object):
    def __init__(self, conn, dts_path, good_commit, bad_commit='HEAD'):
        self.conn = conn
        self.dts_path = dts_path
        self.good_commit = good_commit
        self.bad_commit = bad_commit
        self.bisect_flag = False
        out = self.conn.ssh.exec_command('ls -d %s 2>&1' % self.dts_path)
        if self.dts_path not in out[1].read().decode():
            raise Exception("dts path %s not exist" % self.dts_path)

    def prepare_dpdk(self):
        print("preparing dpdk...")
        self.conn.send_expect('cd %s' % self.dts_path, "# ")
        out = self.conn.send_expect("cd dep; rm -rf dpdk; tar -xzf dpdk.tar.gz", "# ")
        # print(out)
        self.conn.send_expect("cd dpdk", "# ")
        self.conn.send_expect("git clean -xdf", "# ")
        self.conn.send_expect("git checkout master", "# ")
        self.conn.send_expect("git checkout .", "# ")
        out = self.conn.send_expect("git bisect start %s %s" % (self.bad_commit, self.good_commit), "# ")
        self.bisect_flag = True
        # print(out)
        out = self.conn.send_expect("cd ../; rm -rf dpdk.tar.gz; tar -czf dpdk.tar.gz dpdk", "# ")
        self.conn.send_expect("cd %s" % self.dts_path, "# ")
        # print(out)

    def start_dts(self, casename, timeout=600):
        self.conn.send_expect("./dts -t %s" % casename, "DTS ended", timeout=timeout)
        # print(out1)
        # out2 = self.conn.send_expect("cat output/test_results.json", "# ")
        # res_p = re.compile('%s":\s+"(\w+)"' % casename)
        # if not res_p.search(out2):
        #     raise Exception("test case %s failed to get result, please check!" % casename)
        out = self.conn.send_expect("sed -n '/%s/p' output/test_results.json |awk -F ' ' '{print $2}'" % casename, "# ")
        res_p = re.compile('"(\w+)"')
        m = res_p.search(out)
        if not m:
            raise Exception("test case %s failed to get result, please check!" % casename)
        res = m.group(1)
        return res

    def verify_case(self, res):
        check_p = re.compile('(\w+)\s+is the first bad commit')
        self.conn.send_expect("cd dep/dpdk", "#")
        if res == "passed":
            out = self.conn.send_expect("git bisect good", "# ")
            # print(out)
            m = check_p.search(out)
            if not m:
                self.conn.send_expect("cd ../; rm -rf dpdk.tar.gz; tar -czf dpdk.tar.gz dpdk", "# ")
                self.conn.send_expect("cd %s" % self.dts_path, "# ")
            else:
                first_bad = m.group(1)
                return first_bad
        elif res == "failed":
            out = self.conn.send_expect("git bisect bad", "# ")
            # print(out)
            if "is the first bad commit" not in out:
                self.conn.send_expect("cd ../; rm -rf dpdk.tar.gz; tar -czf dpdk.tar.gz dpdk", "# ")
                self.conn.send_expect("cd %s" % self.dts_path, "# ")
            else:
                first_bad = check_p.search(out).group(1)
                return first_bad
        else:
            raise Exception("test case might not run normally")

    def get_commit(self, casename, timeout=3600):
        self.prepare_dpdk()
        commit = None
        t0 = time.time()
        end_time = t0 + float(timeout)
        count = 0
        while not commit and end_time > time.time():
            print("try %d times" % (count+1))
            res = self.start_dts(casename)
            commit = self.verify_case(res)
            count+=1
        if end_time < time.time() and not commit:
            raise Exception("with %s seconds not found bad commit id" % timeout)
        else:
            print("\nafter tried %s times, and takes %s seconds" % (count, time.time()-t0))
            print("FIRST BAD COMMIT: %s" % commit)
            return commit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--testcase', help="case to test")
    parser.add_argument('-p', '--dts_path', help="dts absolute path")
    parser.add_argument('-g', '--good_commit', help="latest good commit id")
    parser.add_argument('-i', '--hostname', help="tester ip")
    parser.add_argument('--timeout', default=3600, help="if the good commit is too far, you can configure more time to findout bad commit. the default timeout is 1 hour")
    args = parser.parse_args()
    conn = Conn(hostname=args.hostname)
    check = CheckCommit(conn, dts_path=args.dts_path, good_commit=args.good_commit)
    check.get_commit(args.testcase, timeout=args.timeout)

