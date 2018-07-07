# -*- coding: utf-8 -*-
from meta.setting import ConfigManager

"""
input:  dict
output: dict filter by model configuration
"""
class DataModel(object):
    def __init__(self):
        confm = ConfigManager()
        self._model_cfgs = confm.get_spider_config(confm.spidername)['model']
        self._models_must_cols = DataModel._gen_must_cols(self._model_cfgs)

    @staticmethod
    def _gen_must_cols(modelcfgs):
        must_cols = {}
        for m in modelcfgs:
            cfg = modelcfgs[m]['fields']
            must_cols[m] = [k for k in cfg if cfg[k]]
        return must_cols

    """
    根据models配置, 分别生成对应的dict数据, 实际上是dict的过滤过程
    """
    def gen_model_data(self, models, dataset):
        if not (models and dataset):
            return None
        def make_unicode_data(x):
            if isinstance(x, unicode):
                return x
            else:
                return unicode(x)
        data_output = dict()
        for m in models:
            dataset_output = []
            for data in dataset:
                must_data_exist = True
                for colname in self._models_must_cols[m]:
                    if colname not in data:
                        must_data_exist = False
                        break
                if must_data_exist:
                    cfg = self._model_cfgs[m]['fields']
                    dataset_output.append({col:make_unicode_data(data[col]) for col in cfg if col in data})
            data_output[m] = dataset_output
        return data_output
