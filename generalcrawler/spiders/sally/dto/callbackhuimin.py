# -*- coding: utf-8 -*-
import json
from callbackcommon import BaseCallback

class HuiminCallback(BaseCallback):
    def __init__(self):
        BaseCallback.__init__(self)
        self.sitename = 'pcshop.huimin100.cn'
        self.cate_id_name_dict = {'17': u'果汁饮料', '18': u'碳酸饮料', '19': u'茶饮料', '20': u'水功能饮料'}

    def convert_data(self, data):
        data = json.loads(data)
        div_start = data.find('<div')
        div_end = data.rfind('</div>') + len('</div>')
        return data[div_start:div_end]

    def calc_product_url(self, productid):
        return 'https://pcshop.huimin100.cn/index.php/home/goods/getsingleitemdetail/uniqueId/' + str(productid)

    def calc_cate_name(self, cate_id):
        if cate_id in self.cate_id_name_dict:
            return self.cate_id_name_dict[cate_id]
        return ''

    def login_url_generator(self, data, dmaps):
        #return information for data_http crawler
        next_run_infos = []
        for k, v in self.cate_id_name_dict.iteritems():
            dmapsi = {'%PAGEINDEX%': '1', '%CATEGORYID%': k}
            tipsi = v + ' Page 1'
            next_run_infos.append((tipsi, self.sitename, 'data_http', dmapsi, 0))
        return next_run_infos

    def data_url_generator(self, data, dmaps):
        if data:
            pageidx = int(dmaps['%PAGEINDEX%'])
            pageidx += 1
            dmaps['%PAGEINDEX%'] = str(pageidx)
            cate_id = dmaps['%CATEGORYID%']
            tips = 'Category id ERROR!'
            if cate_id in self.cate_id_name_dict:
                tips = ''.join([self.cate_id_name_dict[cate_id], ' page ', str(pageidx)])
            return [(tips, self.sitename, 'data_http', dmaps, 0)]
        return None