# -*- coding: utf-8 -*-
import os
import yaml
import datetime
import json
import lxml.html
import copy
from requests.models import Response
from orchestration.parser import Parser
from meta.runner import Runner

class AutohomeParser(Parser):
    def __init__(self):
        super(AutohomeParser, self).__init__()
        self.cur_spider_dir = os.path.dirname(os.path.abspath(__file__))
        self.sitename = 'car.autohome.com.cn'
        city_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'cityinfo.txt'])
        self._cityJsonData = json.load(open(city_file_path))
        city_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'cityname.txt'])
        cityname_list = yaml.load(open(city_file_path))
        self.cityJsonData = [cityinfo for cityinfo in self._cityJsonData if cityinfo['CityName'] in cityname_list]

    def init_runners(self):
        brand_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'brandlist.txt'])
        brandl = []
        with open(brand_file_path) as infile:
            prefixs = 'https://car.autohome.com.cn/price/brand-'
            sufixs = '.html'
            brandl = [line.strip().replace(prefixs,'').replace(sufixs,'') for line in infile]
        runners = []
        for brandid in brandl:
            refdict = {'%BRANDID%': brandid}
            tips = '<' + brandid + '> - page 1 '
            r = Runner(self.sitename+'>brand', refdict, prompt_msg=tips)
            runners.append(r)
        return runners

    def is_response_success(self, runner, rsp):
        return rsp.status_code==200

    def handle_response_error(self, runner, rsp):
        return u'!!! FAILED, STATUS_CODE: {0}, {1}\n{2}'.format(rsp.status_code, runner.get_prompt_msg(), runner.get_url())

    def generate_more_page(self, runner, rsp, dataset):
        runners = []
        if runner.id=='car.autohome.com.cn>brand':
            runners = self._brand_url_generator(runner, rsp.text)
        return runners

    def clean_response_data(self, runner, rsp):
        if isinstance(rsp, Response):
            data = rsp.text
        else:
            data = rsp
        if runner.id=='car.autohome.com.cn>price':
            return self._clean_price_json(data)
        return data



    def _brand_url_generator(self, runner, data):
        runners = []
        if data:
            #dmaps = runner._pass_through
            html = lxml.html.fromstring(data)
            #series run info
            brandid = runner.get_data_viakey('%BRANDID%') #dmaps['%BRANDID%']
            div_xpath = '//div[@class="list-cont-main"]'
            divs = html.xpath(div_xpath)
            for div in divs:
                seriesid_xpath = './div[@class="main-title"]/@id'
                series_spans = div.xpath(seriesid_xpath)
                if len(series_spans)>0:
                    #series run info
                    seriesid = ''.join(series_spans)[1:]
                    tips = '<Brand %s - Series %s> - page 1' % (brandid, seriesid)
                    new_dmaps = dict()
                    new_dmaps['%BRANDID%'] = brandid
                    new_dmaps['%SERIESID%'] = seriesid
                    r = Runner(self.sitename+'>series', new_dmaps, tips)
                    runners.append(r)
                    #dealer run info
                    dealer_dmaps = dict()
                    dealer_dmaps['%SERIESID%'] = seriesid
                    for cityinfo in self.cityJsonData:
                        cityid = str(cityinfo['CityId'])
                        cityname = cityinfo['CityName']
                        tips1 = '<Series %s city %s dealer info> - page 1' % (seriesid, cityname)
                        tips2 = '<Series %s city %s dealer price> - page 1' % (seriesid, cityname)
                        new1_dmaps = copy.deepcopy(dealer_dmaps)
                        new1_dmaps['%CITYID%'] = cityid
                        new1_dmaps['%PROVINCEID%'] = cityid[0:3] + '000'
                        r = Runner(self.sitename+'>dealer', new1_dmaps, tips1)
                        runners.append(r)
                        #dealer price runinfo
                        new2_dmaps = copy.deepcopy(dealer_dmaps)
                        new2_dmaps['%CITYID%'] = cityid
                        r = Runner(self.sitename+'>price', new2_dmaps, tips2)
                        runners.append(r)
            #next page run info
            next_page_xpath = '//div[@class="price-page"]//a[contains(@class,"page-item-next") and contains(@href,"/price/brand")]/@href'
            next_page_url = ''.join(html.xpath(next_page_xpath))
            if next_page_url:
                prefixs = 'https://car.autohome.com.cn/price/brand-'
                sufixs = '.html'
                next_page_url = 'https://car.autohome.com.cn' + next_page_url
                brandid = next_page_url.replace(prefixs,'').replace(sufixs,'')
                dmaps = copy.deepcopy(runner._pass_through)
                dmaps['%BRANDID%'] = brandid
                tips = '<' + brandid + '> - page 1 '
                r = Runner(self.sitename+'>brand', dmaps, tips)
                runners.append(r)
        return runners

    def _clean_price_json(self, data):
        prefixs = 'LoadDealerPrice('
        return json.loads(data.replace(prefixs,'')[:-1])

    def calc_today(self, runner):
        return str(datetime.date.today())

    def calc_brandid(self, runner, brandidinfo):
        prefixs = '/price/brand-'
        sufixs = '.html'
        return brandidinfo.replace(prefixs,'').replace(sufixs,'')

    def calc_seriesid(self, runner, seriesidinfo):
        #s1234, return 1234
        return seriesidinfo[1:]

    def calc_carcolorbg(self, runner, carcolorbginfo):
        return carcolorbginfo.replace('background:','').replace(';','').replace(' ','')

    def calc_specid(self, runner, specidinfo):
        return specidinfo[1:]

    def calc_seriesid_byurl(self, runner, seriesidurlinfo):
        prefixs = '//www.autohome.com.cn/'
        return seriesidurlinfo.replace(prefixs,'').split('/')[0]

    def calc_focusrank(self, runner, userfocusrankinfo):
        return userfocusrankinfo.replace('width:','')

    def calc_dealerid(self, runner, dealeridinfo):
        prefixs = '//dealer.autohome.com.cn/'
        return dealeridinfo.replace(prefixs,'').split('/')[0]
