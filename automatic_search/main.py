#!/usr/bin/env python3

import os
import re
import sys
import pdb
import shutil
from as_cfg_parsing import CommitCfg
from as_ssh_session import SshSession

# os.chdir("../")
cwd = os.getcwd()
sys.path.append(cwd + '/dep')
sys.path.append(cwd + '/cfg')

test_case = 'test_func_reentrancy'
tester_ip = '10.240.179.31'


def run_dts_test(test_commit):
    result = 'bad'
    dts_dpdk = '../dep/dpdk.tar.gz'
    if os.path.isfile(dts_dpdk):
        os.system('rm -rf {}'.format(dts_dpdk))
    shutil.copy('./dep/dpdk.tar.gz', dts_dpdk)
    os.chdir("../dep/")
    os.system('tar -xzf dpdk.tar.gz')
    os.chdir("./dpdk")
    cmd = 'git clean -df'
    os.system(cmd)
    cmd = 'git checkout .'
    os.system(cmd)
    cmd = 'git checkout {}'.format(test_commit)
    os.system(cmd)
    os.system('pwd')
    os.chdir("../")
    os.system('tar -czf dpdk.tar.gz dpdk')
    os.chdir(cwd)
    os.chdir('../')
    os.system('./dts -t {}'.format(test_case))
    with open('./output/test_results.json', 'r') as f:
        for lines in f:
            if 'passed' in lines:
                result = 'good'
                break
            else:
                result = 'bad'
    f.close()
    os.chdir(cwd)
    return result


def auto_search():
    commit_list = []
    if os.path.exists('./dep/dpdk'):
        os.system('rm -rf dep/dpdk')
    local_session = SshSession(tester_ip, 'root', 'tester')
    local_session.send_expect('pwd', '#')
    local_session.send_expect('cd {}'.format(cwd), '#')
    local_session.send_expect('rm -rf dep/dpdk', '#')
    local_session.send_expect('cd dep', '#')
    local_session.send_expect('tar -xzf dpdk.tar.gz', '#')
    local_session.send_expect('cd dpdk', '#')
    local_session.send_expect("""http_proxy=http://proxy-prc.intel.com:911""", '#')
    local_session.send_expect("""http_proxys=http://proxy-prc.intel.com:911""", '#')

    commit = CommitCfg()
    commit_cfg = commit.load_config_file()
    good = commit_cfg[0]['good']
    bad = commit_cfg[0]['bad']
    local_session.send_expect('git bisect start', '#')
    local_session.send_expect('git bisect good {}'.format(good), '#')
    out = local_session.send_expect('git bisect bad {}'.format(bad), '#')

    while 'is the first bad commit' not in out:
        new_commit = re.findall(r'[[](.*?)[]]', out)
        rst = run_dts_test(new_commit[0])
        commit_rst = {'{}'.format(new_commit[0]): '{}'.format(rst)}
        commit_list.append(commit_rst)
        if rst == 'bad':
            out = local_session.send_expect('git bisect bad {}'.format(new_commit[0]), '#')
        else:
            out = local_session.send_expect('git bisect good {}'.format(new_commit[0]), '#')
    local_session.send_expect('git bisect reset', '#')
    print(out)
    print(commit_list)
    local_session.close_session()
    return


def main():
    auto_search()


if __name__ == '__main__':
    main()
