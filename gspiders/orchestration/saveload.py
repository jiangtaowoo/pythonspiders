# -*- coding: utf-8 -*-
import os
from meta.setting import ConfigManager


"""
将生成的Model数据, 保存到指定的存储设备中
存储设备可能是 RMDB, redis, MongoDB, file 等等
"""
class SaveLoader(object):
    def __init__(self, spidername=''):
        if spidername:
            confm = ConfigManager(spidername)
        else:
            confm = ConfigManager()
        self._cfgs = confm.get_spider_config(confm.spidername)['persist']
        self._models = confm.get_spider_config(confm.spidername)['model']

    def get_storage_config(self, modelname):
        if self._cfgs and modelname in self._cfgs:
            cfg = self._cfgs[modelname]
            dbfile = cfg['storage']['file']
            dbscheme = cfg['storage']['scheme']
            dbtable = cfg['storage']['table']
            model = self._models[modelname]
            fieldicts = model['fields']
            pks = model['PK']
            return (dbfile, dbscheme, dbtable, fieldicts, pks)
        return None

    def is_update_policy(self, modelname):
        if modelname in self._cfgs:
            cfg = self._cfgs[modelname]
            if 'policy' in cfg:
                return cfg['policy']=='update'
        return False

    def persist_data(self, modeldatas):
        if modeldatas:
            for m in modeldatas:
                dataset = modeldatas[m]
                for data in dataset:
                    if not self.is_data_exists(m, data):
                        self.save(m, data)
                    elif self.is_update_policy(m):
                        self.update(m, data)

    """
    the following procedure should be override
    """
    def is_data_exists(self, modelname, data):
        return False

    def save(self, modelname, data):
        result = self.get_storage_config(modelname)
        dbfile = result[0] if result else modelname
        if not os.path.exists(dbfile):
            with open(dbfile, 'w') as outfile:
                outfile.write('\t'.join([x.encode('utf-8') for x in data]))
                outfile.write('\n')
        with open(dbfile, 'a+') as outfile:
            outfile.write('\t'.join([data[x].encode('utf-8') for x in data]))
            outfile.write('\n')

    def update(self, modelname, data):
        pass

    def load_data(self, modelname, filter_kwargs):
        pass
