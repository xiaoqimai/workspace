#!usr/bin/python3


import paramiko
import time
import os


class Conn(object):
    def __init__(self, hostname, username, password, port=22, timeout=10, buff=1024, verbose=False):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.buff = buff
        self.verbose = verbose
        self.ssh = paramiko.SSHClient()
        self.__get_conn()

    def __get_conn(self):
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password,
                             timeout=self.timeout, allow_agent=False)
            self.chan = self.ssh.invoke_shell(width=1024, height=1024)
            time.sleep(1)
            self._clean_before()
        except Exception as e:
            print("connect to host {hostname} failed!".format(hostname=self.hostname))
            raise (e)

    def close(self):
        self.chan.shutdown(how=2)
        self.ssh.close()

    def _clean_before(self, buff=102400):
        if self.chan.recv_ready():
            tmp = self.chan.recv(nbytes=buff).decode("utf-8")
            print("before info>>>\n %s " % tmp)

    def send_command(self, cmd, timeout=3):
        self._clean_before()
        time.sleep(0.2)
        if self.chan.send_ready():
            self.chan.send(cmd + os.linesep)
            out = ""
            end_time = time.time() + timeout
            while end_time - time.time() >= 0:
                time.sleep(0.5)
                if self.chan.recv_ready():
                    tmp = self.chan.recv(self.buff).decode("utf-8")
                    if self.verbose:
                        print(tmp)
                    out = out + tmp
            return out

    def send_expect(self, cmd, exp, timeout=15):
        self._clean_before()
        if self.chan.send_ready():
            self.chan.send(cmd + os.linesep)
            out = ""
            verify_line = ""
            end_time = time.time() + timeout
            while not exp in verify_line:
                if self.chan.recv_ready():
                    tmp = self.chan.recv(self.buff).decode("utf-8")
                    if self.verbose:
                        print(tmp, end='')
                    out = out + tmp
                    output_line = out.split(os.linesep)
                    last_line = -1
                    while output_line[last_line] == '':
                        last_line -= 1
                    verify_line = output_line[last_line]
                if end_time - time.time() >= 0:
                    continue
                elif exp not in verify_line:
                    print("TIME OUT: output is: %s" % out)
                    raise TimeoutError
            return out


if __name__ == '__main__':
    conn = Conn("10.240.179.71", "root", "tester", verbose=False)
    out = conn.send_expect("scapy", exp=">>> ", timeout=3)
    print(out)
    out = conn.send_expect(chr(4), exp="# ", timeout=3)
    print(out)
    out2 = conn.send_command(
        "sendp(Ether(dst='3c:fd:fe:9d:ab:b0')/IP()/Raw(load='xxx'*60), iface='enp1s0f0', inter=0.5, count=10)",
        timeout=3)
    out3 = conn.send_expect(
        "sendp(Ether(dst='3c:fd:fe:9d:ab:b0')/IP()/Raw(load='xxx'*60), iface='enp1s0f0', inter=0.5, count=10)",
        exp='>>> ', timeout=3)
    print(out3)
    conn.close()
