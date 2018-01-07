# -*- coding: utf-8 -*-
import os
import yaml

class BaseDTO(object):
    def __init__(self):
        self._dto_cfgs = []

    def _get_sitedto_from_sitename(self, sitename):
        if sitename in self._dto_cfgs:
            return self._dto_cfgs[sitename]
        return None

    def load_dto_config(self, dto_cfg_file_path):
        if os.path.exists(dto_cfg_file_path):
            self._dto_cfgs = yaml.load(open(dto_cfg_file_path, 'r'))
            return True
        return False

    def parse_data(self, sitename, data, dmaps):
        return data