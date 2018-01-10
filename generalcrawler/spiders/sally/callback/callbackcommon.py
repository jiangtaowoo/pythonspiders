# -*- coding: utf-8 -*-
import os
import datetime
import yaml

class BaseCallback(object):
    def __init__(self):
        self._brand_data = None
        self._taste_data = None
        self._load_brand_taste_cfg(os.path.sep.join(['.', 'config', 'taste.yaml']))

    def _load_brand_taste_cfg(self, brand_taste_cfg_file):
        if os.path.exists(brand_taste_cfg_file):
            brand_taste_data = yaml.load(open(brand_taste_cfg_file))
            self._brand_data = brand_taste_data['brand']
            self._taste_data = brand_taste_data['taste']
            self._brand_data.sort(key=lambda x: -len(x))
            self._taste_data.sort(key=lambda x: -len(x))

    def map_today(self):
        return str(datetime.date.today())

    def map_product_brand(self, productname):
        for b in self._brand_data:
            if b in productname:
                return b
        return ''

    def map_product_taste(self, productname):
        for tas in self._taste_data:
            if tas in productname:
                return tas
        return ''

    def map_product_spec(self, productsize, idx):
        if productsize:
            details = productsize.replace(u'×','*').split('*')
            idx = int(idx)
            if idx < len(details):
                if idx<2:
                    return details[idx]
                else:
                    return ''.join(details[idx:])
        return ''