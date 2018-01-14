# -*- coding: utf-8 -*-
import os
import datetime
import json
import lxml.html
import copy
{%- for CLS_NAME, CLS_INFO in JJ2_sitecbs.items() %}


class {{ CLS_NAME }}(object):
    def __init__(self):
        self.sleepinterval = 0
        self.cur_spider_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        {%- for SITE_HTTP in JJ2_sitecbnames[CLS_NAME] %}
        self.sitename = '{{SITE_HTTP}}'
        {%- endfor %}

    def convert_data(self, data, dmaps):
        return data

    def init_url_generator(self, data, dmaps):
        next_run_info = []
        tips = ''
        newdmaps = dict()
        next_run_info.append((tips, self.sitename, 'data_http', newdmaps, self.sleepinterval))
        return next_run_info

    def data_url_generator(self, data, dmaps):
        if data:
            param1 = dmaps['%PARAM%']
            param1 = param1 + 1
            dmaps['%PARAM%'] = param1
            tips = ''
            return [(tips, self.sitename, 'data_http', dmaps, self.sleepinterval)]
        return None

    {%- for FUNC_NAME, FUNC_PARAM_LIST in CLS_INFO.items() %}

    def {{ FUNC_NAME }}(self, dmaps{%- for PARAM_NAME in FUNC_PARAM_LIST %}, {{PARAM_NAME}} {%- endfor %}):
        return None
    {%- endfor %}
{%- endfor %}