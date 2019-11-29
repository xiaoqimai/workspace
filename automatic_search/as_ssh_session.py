#!/usr/bin/env python3

from pexpect import pxssh


class SshSession(object):
    def __init__(self, host, username, password):
        self.magic_prompt = "MAGIC PROMPT"
        self.logger = None
        self.session = ""

        self.host = host
        self.username = username
        self.password = password

        self._connect_host()

    def __flush(self):
        self.session.buffer = b''
        self.session.before = b''

    def close_session(self):
        if self.session is None:
            return
        else:
            self.__flush()
            self.session.logout()

    def get_output_all(self):
        output = self.session.before
        string = str(output, 'utf-8')
        string = string.replace("[PEXPECT]", "")
        return string

    def get_session_before(self, timeout=15):
        self.session.PROMPT = self.magic_prompt
        try:
            self.session.prompt(timeout)
        except Exception as e:
            print("{}".format(e))
            pass
        before = self.get_output_all()
        self.__flush()
        return before

    def clean_session(self):
        self.get_session_before(timeout=0.01)

    def __send_line(self, command):
        if len(command) == 2 and command.startswith('^'):
            self.session.sendcontrol(command[1])
        else:
            self.session.sendline(command)

    def __prompt(self, command, timeout):
        if not self.session.prompt(timeout):
            print("TIMEOUT:command:{}".format(command))

    def send_expect_base(self, command, expected, timeout):
        self.clean_session()
        self.session.PROMPT = expected
        self.__send_line(command)
        self.__prompt(command, timeout)

        before = self.get_output_before()
        return before

    def get_output_before(self):
        before = self.session.before
        before = before.replace(b'\r\n', b'')
        string = str(before, 'utf-8')
        string = string.replace("[PEXPECT]", "")
        return string

    def send_expect(self, command, expected, timeout=15, verify=False):
        try:
            ret = self.send_expect_base(command, expected, timeout)
            if verify:
                ret_status = self.send_expect_base("echo $?", expected, timeout)
                if not int(ret_status):
                    return ret
                else:
                    self.logger.error("Command: %s failure!" % command)
                    self.logger.error(ret)
                    return int(ret_status)
            else:
                return ret
        except Exception as e:
            print(e)
            print("Exception happened in [{}] and output is [{}]".format(command, self.get_output_before()))

    def _connect_host(self):
        try:
            self.session = pxssh.pxssh()
            if ':' in self.host:
                self.ip = self.host.split(':')[0]
                self.port = int(self.host.split(':')[1])
                self.session.login(self.ip, self.username,
                                   self.password, original_prompt='[$#>]',
                                   port=self.port, login_timeout=20)
            else:
                self.session.login(self.host, self.username,
                                   self.password, original_prompt='[$#>]')
            self.send_expect('stty -echo', '#')
            self.send_expect('stty columns 1000', "#")
        except Exception as e:
            print(e)
            if getattr(self, 'port', None):
                suggestion = "Suggest: Check if the firewall on [ {} ] ".format(self.ip) + "is stopped"
                print(suggestion)
