# -*- coding: utf-8 -*-
import json
from callbackcommon import BaseCallback

class Dd528Callback(BaseCallback):
    def __init__(self):
        BaseCallback.__init__(self)
        self.sitename = 'www.dd528.com'

    def convert_data(self, data, dmaps):
        return json.loads(data)

    def login_url_generator(self, data, dmaps):
        #return information for data_http crawler
        #(tips, sitename, sitehttp, dmaps, sleepinterval)
        dmaps = {'%PAGEOFFSET%': '0'}
        return [('page 1', self.sitename, 'data_http', dmaps, 0)]       #(tips, sitehttp, dmaps)

    def data_url_generator(self, data, dmaps):
        #(tips, sitename, sitehttp, dmaps, sleepinterval)
        if data:
            pageoff = int(dmaps['%PAGEOFFSET%'])
            pageoff += 100
            dmaps['%PAGEOFFSET%'] = str(pageoff)
            return [('page ' + str(pageoff/100+1), self.sitename, 'data_http', dmaps, 0)]
        return None

    def calc_product_url(self, dmaps, productid):
        return 'http://www.dd528.com/detail?gid=' + str(productid)