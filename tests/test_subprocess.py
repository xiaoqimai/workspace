import subprocess
from framework.conn import Conn
from framework.crb import Crb
import os

class SubProcess(Crb):
    def __init__(self):
        super().__init__(hostname="10.240.179.71", username="root", password="tester")

    def get_session(hostname, username, password, port=22, timeout=10):
        return Conn(hostname=hostname, username=username, password=password, port=port, timeout=timeout)

def run_cmd(cmd):
    os.chdir('/home/dts_work')
    # p = subprocess.Popen('./dts 2>&1|tee -a $(date "+%Y-%m-%d")_dts.log', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
    while True:
        out = p.stdout.readline().decode('utf-8')
        print(out)
        if 'DTS ended' in out or out=='':
            p.kill()
            break
