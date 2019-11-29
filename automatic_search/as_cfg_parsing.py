#!/usr/bin/env python3

import configparser


class UserConf:
    def __init__(self, config):
        self.conf = configparser.SafeConfigParser()
        load_files = self.conf.read(config)
        if load_files is None:
            self.conf = None
            print("Not found file:{}.".format(config))

    def get_sections(self):
        if self.conf is None:
            return None
        return self.conf.sections()

    def load_section(self, section):
        items = None
        if self.conf is None:
            return None
        for conf_sect in self.conf.sections():
            if conf_sect == section:
                items = self.conf.items(section)
        return items


class CommitCfg:
    def __init__(self):
        self.config_file = './cfg/commit.cfg'
        self.commit_cfg = []
        try:
            self.commit_conf = UserConf(self.config_file)
        except Exception as e:
            self.commit_conf = None
            print("Open cfg file failed:{}.".format(e))

    def load_config_file(self):
        commit = {'good': '', 'bad': ''}
        sections = self.commit_conf.get_sections()
        if not sections:
            return self.commit_cfg
        for name in sections:
            commit_conf = self.commit_conf.load_section(name)
            if not commit_conf:
                continue

            for conf in commit_conf:
                key, value = conf
                if key == 'good':
                    commit['good'] = value
                elif key == 'bad':
                    commit['bad'] = value

            self.commit_cfg.append(commit)
        return self.commit_cfg
