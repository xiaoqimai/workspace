#! /usr/bin/python3

import subprocess
import os
import argparse
import re
import json
import configparser
import time


os.chdir('/root/dpdk')
parser = argparse.ArgumentParser('get commit info')
parser.add_argument('-i', '--commit', default='master', help='commit id to compile')
# parser.add_argument('-c', '--cflags', default='O3', help='CFLAGS to compile')
args = parser.parse_args()


def verify(condition, description):
    if not condition:
        raise AssertionError(description)


def exec_cmd(cmd):
    print(cmd)
    res = os.system(cmd)
    verify(res == 0, "execute cmd %s failed" % cmd)


def send_cmd(cmd, timeout=15):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=os.getcwd())
    out_put, error_put = p.communicate(timeout=timeout)
    if error_put:
        print(out_put.decode(), error_put.decode())
        p.kill()
        return (out_put + error_put).decode()
    else:
        print(out_put.decode())
        p.kill()
        return out_put.decode()


def checkout_version(commit_id='master'):
    send_cmd("git clean -xdf")
    send_cmd("git checkout .")
    send_cmd("git checkout %s" % commit_id)
    send_cmd("git checkout .")


def get_cpu_num():
    out = send_cmd('lscpu')
    p = re.compile('CPU\(s\):\s*(\d+)', re.S)
    return int(p.search(out).group(1).strip())


def compile_dpdk(cflags='O3'):
    cpu_num = get_cpu_num() - 2
    cmd = 'rm -rf x86_64-native-linuxapp-gcc;rm -rf ./app/test/test_resource_c.res.o;rm -rf ./app/test/test_resource_tar.res.o;rm -rf ./app/test/test_pci_sysfs.res.o'
    exec_cmd(cmd)
    print("start compiling...")
    build_cmd = "export EXTRA_CFLAGS='-%s'; export RTE_TARGET=x86_64-native-linuxapp-gcc;export RTE_SDK=`pwd`;make -j%s install T=x86_64-native-linuxapp-gcc" % (cflags, cpu_num)
    out = send_cmd(build_cmd, timeout=600)
    if not re.search('[E|e]rror\s\d+', out):
        return True
    else:
        return False

def record_compile_result(result, log_path):
    # res = [["gcc version", "dpdk version", "cflags", "compile status"]]
    with open(log_path, 'a+') as f:
        json.dump(result, f)


def main():
    print("dpdk version: %s" % args.commit)
    checkout_version(commit_id=args.commit)
    out = send_cmd("gcc --version")
    gcc_version = out.splitlines()[0]
    log_path = "/root/dpdk_compile_test_%s.log" % (time.strftime("%Y-%m-%d"))

    for cflag in ["O3", "O2", "O1", "O0"]:
        res = compile_dpdk(cflags=cflag)
        print("cflas %s to compile" % cflag)
        compile_log = {}
        compile_log["gcc version:"] = gcc_version
        compile_log["dpdk version:"] = args.commit
        compile_log["cflags"] = cflag
        compile_log["compile status"] = "Success" if res else "Failed"
        record_compile_result(compile_log, log_path=log_path)


if __name__ == '__main__':
    main()
