# -*- coding: utf-8 -*-
import os
import datetime
import json
import lxml.html
import copy


class NDSCallback(object):
    def __init__(self):
        self.sitename = 'shop.nordstrom.com'
        self.cur_spider_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _recursive_makedirs(self, dir_chain):
        #create sub dir inside current spider dir
        dir_l = filter(len,dir_chain.split(os.path.sep))
        cur_dir = self.cur_spider_dir
        for subdir in dir_l:
            cur_dir = cur_dir + os.path.sep + subdir
            if not os.path.exists(cur_dir):
                os.makedirs(cur_dir)

    def _calc_url_for_browser(self, dmaps):
        k1 = '%CATAL3%'
        k2 = '%CM_SP_INFO%'
        k3 = '%PAGEINDEX%'
        if k1 in dmaps and k2 in dmaps and k3 in dmaps:
            url_iteml = []
            url_iteml.append('https://shop.nordstrom.com/c/')
            url_iteml.append(dmaps['%CATAL3%'])
            url_iteml.append('?origin=topnav&cm_sp=')
            url_iteml.append(dmaps['%CM_SP_INFO%'])
            url_iteml.append('&page=')
            url_iteml.append(dmaps['%PAGEINDEX%'])
            url_iteml.append('&top=72')
            return ''.join(url_iteml)
        return ''

    def _calc_cur_dmaps_tips(self, dmaps):
        catainfo = []
        catainfo.append(dmaps['%CATAL1%'])
        catainfo.append(dmaps['%CATAL2%'])
        catainfo.append(dmaps['%CATAL3%'])
        pageidx = int(dmaps['%PAGEINDEX%'])
        tips = '<' + ' - '.join(catainfo) + '> - page %d ' % (pageidx)
        return tips

    def _update_dmaps_next_page(self, dmaps):
        pageidx = int(dmaps['%PAGEINDEX%'])
        pageidx += 1
        dmaps['%PAGEINDEX%'] = str(pageidx)
        dmaps['%PRODUCT_URL%'] = self._calc_url_for_browser(dmaps)

    def convert_data(self, data, dmaps):
        #try:
        return json.loads(data)
        #except:

    def init_url_generator(self, data, dmaps):
        cata_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'catalist.txt'])
        catal = []
        with open(cata_file_path) as infile:
            for line in infile:
                cataline = line.strip().split('|')
                catal.append(cataline)
        next_run_info = []
        for cataline in catal:
            newdmaps = dict()
            newdmaps['%SITENAME%'] = 'NordStrom'
            newdmaps['%CATAL1%'] = cataline[0]
            newdmaps['%CATAL2%'] = cataline[1]
            newdmaps['%CATAL3%'] = cataline[2]
            newdmaps['%CATAL3_NAME%'] = cataline[3]
            newdmaps['%CM_SP_INFO%'] = cataline[4]
            newdmaps['%PAGEINDEX%'] = '1'
            newdmaps['%PRODUCT_URL%'] = self._calc_url_for_browser(newdmaps)
            tips = self._calc_cur_dmaps_tips(newdmaps)
            next_run_info.append((tips, self.sitename, 'browser_http', newdmaps, 0))
            break
        return next_run_info

    def data_url_generator(self, data, dmaps):
        if data:
            self._update_dmaps_next_page(dmaps)
            tips = self._calc_cur_dmaps_tips(dmaps)
            return [(tips, self.sitename, 'data_http', dmaps, 0)]
        return None

    def browser_url_generator(self, data, dmaps):
        html = lxml.html.fromstring(data)
        next_page_xpath = '//a[@class="npr-1o-ZR"]/span/text()'
        divs = html.xpath(next_page_xpath)
        if divs:
            for div in divs:
                if 'Next' in div:
                    #has next page
                    self._update_dmaps_next_page(dmaps)
                    tips = self._calc_cur_dmaps_tips(dmaps)
                    return [(tips, self.sitename, 'data_http', dmaps, 0)]
        return None


    def get_prodid_fromhref(self, dmaps, produrl_short):
        #href="/s/rebecca-minkoff-julian-nylon-backpack/4882828?origin=category-p
        ss = produrl_short.split('/')
        if len(ss)>3:
            return ss[3].split('?')[0]
        return ''

    def get_join_color(self, dmaps, prodcolor_info):
        if isinstance(prodcolor_info, list):
            return '|'.join(map(str,prodcolor_info))
        return prodcolor_info

    def get_dmap_param(self, dmaps, dmap_param_key):
        if dmap_param_key in dmaps:
            return dmaps[dmap_param_key]
        return None

    def get_img_url(self, dmaps, prodid, prodimgurl):
        #download img, save to local file, return local file path as current field data
        #local file path = ./IMAGES/L1/L2/L3/prodid_origin_url_imge_file_name
        if prodimgurl:
            newdmaps = dict()
            img_file_name = str(prodid) + prodimgurl.split('/')[-1]
            newdmaps['%CATAL1%'] = dmaps['%CATAL1%']
            newdmaps['%CATAL2%'] = dmaps['%CATAL2%']
            newdmaps['%CATAL3%'] = dmaps['%CATAL3%']
            newdmaps['%FILENAME%'] = img_file_name
            newdmaps['%IMG_URL%'] = prodimgurl
            dir_chain = os.path.sep.join(['IMAGES', newdmaps['%CATAL1%'], newdmaps['%CATAL2%'], newdmaps['%CATAL3%']])
            self._recursive_makedirs(dir_chain)
            img_file_path = os.path.sep.join([self.cur_spider_dir, dir_chain, img_file_name])
            return img_file_path
        return None

    def get_prod_url(self, dmaps, produrl_short):
        #return full url
        #short_url = '/s/herschel-supply-co-sydney-backpack/3579893'
        prefixs = 'https://shop.nordstrom.com'
        return prefixs + produrl_short