# -*- coding: utf-8 -*-
import os
import yaml
from meta.metacls import Singleton

"""
加载配置文件
"""
class ConfigManager(object):
    __metaclass__ = Singleton

    def __init__(self, spidername):
        self._spidername = spidername
        self._cfgs = {spidername: self.load_spider_config(spidername)}

    @staticmethod
    def get_config_path(spidername):
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.sep.join([app_base_dir, 'spiders', spidername, 'config'])

    @staticmethod
    def load_config(filepath):
        if os.path.exists(filepath):
            return yaml.load(open(filepath))
        return None

    def load_spider_config(self, spidername):
        names = ['http', 'dto', 'model', 'persist']
        cfg_path = ConfigManager.get_config_path(spidername)
        cfg_dict = {x: ConfigManager.load_config(os.sep.join([cfg_path,x+'.yaml'])) for x in names}
        return cfg_dict

    def get_spider_config(self, spidername):
        return self._cfgs[spidername]

    @property
    def spidername(self):
        return self._spidername
