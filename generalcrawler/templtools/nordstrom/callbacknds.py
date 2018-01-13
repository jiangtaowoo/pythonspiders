# -*- coding: utf-8 -*-
import os
import datetime
import json
import lxml.html
import copy


class AmazonCallback(object):
    def __init__(self):
        self.sitename = 'www.amazon.com'

    def init_url_generator(self, data, dmaps):
        next_run_info = []
        tips = ''
        newdmaps = dict()
        next_run_info.append((tips, self.sitename, 'data_http', newdmaps, 0))
        return next_run_info

    def data_url_generator(self, data, dmaps):
        if data:
            param1 = dmaps['%PARAM%']
            param1 = param1 + 1
            dmaps['%PARAM%'] = param1
            tips = ''
            return [(tips, self.sitename, 'data_http', dmaps, 0)]
        return None

    def funcxxx(self, colid, datetimex):
        return None


class NDSCallback(object):
    def __init__(self):
        self.sitename = 'shop.nordstrom.com'

    def init_url_generator(self, data, dmaps):
        next_run_info = []
        tips = ''
        newdmaps = dict()
        next_run_info.append((tips, self.sitename, 'data_http', newdmaps, 0))
        return next_run_info

    def data_url_generator(self, data, dmaps):
        if data:
            param1 = dmaps['%PARAM%']
            param1 = param1 + 1
            dmaps['%PARAM%'] = param1
            tips = ''
            return [(tips, self.sitename, 'data_http', dmaps, 0)]
        return None

    def func2(self, colid, colid2):
        return None

    def func(self, colid):
        return None