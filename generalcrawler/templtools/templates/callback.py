# -*- coding: utf-8 -*-
import os
import datetime
import json
import lxml.html
import copy
{%- for CLS_NAME, CLS_INFO in JJ2_sitecbs.items() %}


class {{ CLS_NAME }}(object):
    def __init__(self):
        {%- for SITE_HTTP in JJ2_sitecbnames[CLS_NAME] %}
        self.sitename = '{{SITE_HTTP}}'
        {%- endfor %}

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

    {%- for FUNC_NAME, FUNC_PARAM_LIST in CLS_INFO.items() %}

    def {{ FUNC_NAME }}(self{%- for PARAM_NAME in FUNC_PARAM_LIST %}, {{PARAM_NAME}} {%- endfor %}):
        return None
    {%- endfor %}
{%- endfor %}