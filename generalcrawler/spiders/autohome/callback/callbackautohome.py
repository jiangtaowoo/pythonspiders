# -*- coding: utf-8 -*-
import os
import datetime
#import yaml
import json
import lxml.html
import copy

class AutohomeCallback(object):
    def __init__(self):
        self.cur_spider_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sitename = 'car.autohome.com.cn'
        self._cityJsonData= [{"CityId":440900,"CityName":"茂名","Count":0,"PinYin":"maoming"},{"CityId":110100,"CityName":"北京","Count":24,"PinYin":"beijing"},{"CityId":120100,"CityName":"天津","Count":7,"PinYin":"tianjin"},{"CityId":130100,"CityName":"石家庄","Count":5,"PinYin":"shijiazhuang"},{"CityId":130200,"CityName":"唐山","Count":3,"PinYin":"tangshan"},{"CityId":130300,"CityName":"秦皇岛","Count":1,"PinYin":"qinhuangdao"},{"CityId":130400,"CityName":"邯郸","Count":2,"PinYin":"handan"},{"CityId":130500,"CityName":"邢台","Count":1,"PinYin":"xingtai"},{"CityId":130600,"CityName":"保定","Count":3,"PinYin":"baoding"},{"CityId":130700,"CityName":"张家口","Count":1,"PinYin":"zhangjiakou"},{"CityId":130800,"CityName":"承德","Count":1,"PinYin":"chengde"},{"CityId":130900,"CityName":"沧州","Count":2,"PinYin":"cangzhou"},{"CityId":131000,"CityName":"廊坊","Count":1,"PinYin":"langfang"},{"CityId":131100,"CityName":"衡水","Count":1,"PinYin":"hengshui"},{"CityId":140100,"CityName":"太原","Count":4,"PinYin":"taiyuan"},{"CityId":140200,"CityName":"大同","Count":1,"PinYin":"datong"},{"CityId":140300,"CityName":"阳泉","Count":1,"PinYin":"yangquan"},{"CityId":140700,"CityName":"晋中","Count":1,"PinYin":"jinzhong"},{"CityId":140800,"CityName":"运城","Count":1,"PinYin":"yuncheng"},{"CityId":141000,"CityName":"临汾","Count":1,"PinYin":"linfen"},{"CityId":141100,"CityName":"吕梁","Count":1,"PinYin":"lvliang"},{"CityId":150100,"CityName":"呼和浩特","Count":3,"PinYin":"huhehaote"},{"CityId":150200,"CityName":"包头","Count":2,"PinYin":"baotou"},{"CityId":150400,"CityName":"赤峰","Count":1,"PinYin":"chifeng"},{"CityId":150500,"CityName":"通辽","Count":1,"PinYin":"tongliao"},{"CityId":150600,"CityName":"鄂尔多斯","Count":2,"PinYin":"eerduosi"},{"CityId":150700,"CityName":"呼伦贝尔","Count":1,"PinYin":"hulunbeier"},{"CityId":150800,"CityName":"巴彦淖尔","Count":1,"PinYin":"bayannaoer"},{"CityId":210100,"CityName":"沈阳","Count":6,"PinYin":"shenyang"},{"CityId":210200,"CityName":"大连","Count":4,"PinYin":"dalian"},{"CityId":210300,"CityName":"鞍山","Count":2,"PinYin":"anshan"},{"CityId":210600,"CityName":"丹东","Count":1,"PinYin":"dandong"},{"CityId":210700,"CityName":"锦州","Count":1,"PinYin":"jinzhou"},{"CityId":210800,"CityName":"营口","Count":1,"PinYin":"yingkou"},{"CityId":210900,"CityName":"阜新","Count":1,"PinYin":"fuxin"},{"CityId":211000,"CityName":"辽阳","Count":1,"PinYin":"liaoyang"},{"CityId":211100,"CityName":"盘锦","Count":1,"PinYin":"panjin"},{"CityId":211200,"CityName":"铁岭","Count":1,"PinYin":"tieling"},{"CityId":211300,"CityName":"朝阳","Count":1,"PinYin":"chaoyang"},{"CityId":211400,"CityName":"葫芦岛","Count":1,"PinYin":"huludao"},{"CityId":220100,"CityName":"长春","Count":4,"PinYin":"changchun"},{"CityId":220200,"CityName":"吉林","Count":2,"PinYin":"jilinshi"},{"CityId":220500,"CityName":"通化","Count":1,"PinYin":"tonghua"},{"CityId":220700,"CityName":"松原","Count":1,"PinYin":"songyuan"},{"CityId":222400,"CityName":"延边","Count":1,"PinYin":"yanbian"},{"CityId":230100,"CityName":"哈尔滨","Count":5,"PinYin":"haerbin"},{"CityId":230200,"CityName":"齐齐哈尔","Count":1,"PinYin":"qiqihaer"},{"CityId":230600,"CityName":"大庆","Count":1,"PinYin":"daqing"},{"CityId":230800,"CityName":"佳木斯","Count":1,"PinYin":"jiamusi"},{"CityId":231000,"CityName":"牡丹江","Count":1,"PinYin":"mudanjiang"},{"CityId":231200,"CityName":"绥化","Count":1,"PinYin":"suihua"},{"CityId":310100,"CityName":"上海","Count":17,"PinYin":"shanghai"},{"CityId":320100,"CityName":"南京","Count":7,"PinYin":"nanjing"},{"CityId":320200,"CityName":"无锡","Count":9,"PinYin":"wuxi"},{"CityId":320300,"CityName":"徐州","Count":3,"PinYin":"xuzhou"},{"CityId":320400,"CityName":"常州","Count":4,"PinYin":"changzhou"},{"CityId":320500,"CityName":"苏州","Count":9,"PinYin":"suzhou"},{"CityId":320600,"CityName":"南通","Count":3,"PinYin":"nantong"},{"CityId":320700,"CityName":"连云港","Count":1,"PinYin":"lianyungang"},{"CityId":320800,"CityName":"淮安","Count":1,"PinYin":"huaian"},{"CityId":320900,"CityName":"盐城","Count":3,"PinYin":"yancheng"},{"CityId":321000,"CityName":"扬州","Count":2,"PinYin":"yangzhou"},{"CityId":321100,"CityName":"镇江","Count":1,"PinYin":"zhenjiang"},{"CityId":321200,"CityName":"泰州","Count":3,"PinYin":"tai_zhou"},{"CityId":321300,"CityName":"宿迁","Count":1,"PinYin":"suqian"},{"CityId":330100,"CityName":"杭州","Count":11,"PinYin":"hangzhou"},{"CityId":330200,"CityName":"宁波","Count":9,"PinYin":"ningbo"},{"CityId":330300,"CityName":"温州","Count":9,"PinYin":"wenzhou"},{"CityId":330400,"CityName":"嘉兴","Count":4,"PinYin":"jiaxing"},{"CityId":330500,"CityName":"湖州","Count":3,"PinYin":"huzhou"},{"CityId":330600,"CityName":"绍兴","Count":6,"PinYin":"shaoxing"},{"CityId":330700,"CityName":"金华","Count":5,"PinYin":"jinhua"},{"CityId":330800,"CityName":"衢州","Count":1,"PinYin":"quzhou"},{"CityId":330900,"CityName":"舟山","Count":1,"PinYin":"zhoushan"},{"CityId":331000,"CityName":"台州","Count":6,"PinYin":"taizhou"},{"CityId":331100,"CityName":"丽水","Count":1,"PinYin":"lishui"},{"CityId":340100,"CityName":"合肥","Count":4,"PinYin":"hefei"},{"CityId":340200,"CityName":"芜湖","Count":1,"PinYin":"wuhu"},{"CityId":340300,"CityName":"蚌埠","Count":1,"PinYin":"bangbu"},{"CityId":340500,"CityName":"马鞍山","Count":1,"PinYin":"maanshan"},{"CityId":340600,"CityName":"淮北","Count":1,"PinYin":"huaibei"},{"CityId":340700,"CityName":"铜陵","Count":1,"PinYin":"tongling"},{"CityId":340800,"CityName":"安庆","Count":1,"PinYin":"anqing"},{"CityId":341100,"CityName":"滁州","Count":1,"PinYin":"chuzhou"},{"CityId":341200,"CityName":"阜阳","Count":1,"PinYin":"fu_yang"},{"CityId":341300,"CityName":"宿州","Count":1,"PinYin":"su_zhou"},{"CityId":341500,"CityName":"六安","Count":1,"PinYin":"liuan"},{"CityId":341600,"CityName":"亳州","Count":1,"PinYin":"bozhou"},{"CityId":350100,"CityName":"福州","Count":5,"PinYin":"fuzhou"},{"CityId":350200,"CityName":"厦门","Count":3,"PinYin":"xiamen"},{"CityId":350300,"CityName":"莆田","Count":1,"PinYin":"putian"},{"CityId":350400,"CityName":"三明","Count":1,"PinYin":"sanming"},{"CityId":350500,"CityName":"泉州","Count":4,"PinYin":"quanzhou"},{"CityId":350600,"CityName":"漳州","Count":1,"PinYin":"zhangzhou"},{"CityId":350800,"CityName":"龙岩","Count":1,"PinYin":"longyan"},{"CityId":350900,"CityName":"宁德","Count":1,"PinYin":"ningde"},{"CityId":360100,"CityName":"南昌","Count":3,"PinYin":"nanchang"},{"CityId":360400,"CityName":"九江","Count":1,"PinYin":"jiujiang"},{"CityId":360700,"CityName":"赣州","Count":1,"PinYin":"ganzhou"},{"CityId":360800,"CityName":"吉安","Count":1,"PinYin":"jian"},{"CityId":360900,"CityName":"宜春","Count":1,"PinYin":"yi_chun"},{"CityId":361000,"CityName":"抚州","Count":1,"PinYin":"fu_zhou"},{"CityId":370100,"CityName":"济南","Count":3,"PinYin":"jinan"},{"CityId":370200,"CityName":"青岛","Count":5,"PinYin":"qingdao"},{"CityId":370300,"CityName":"淄博","Count":2,"PinYin":"zibo"},{"CityId":370400,"CityName":"枣庄","Count":1,"PinYin":"zaozhuang"},{"CityId":370500,"CityName":"东营","Count":2,"PinYin":"dongying"},{"CityId":370600,"CityName":"烟台","Count":2,"PinYin":"yantai"},{"CityId":370700,"CityName":"潍坊","Count":4,"PinYin":"weifang"},{"CityId":370800,"CityName":"济宁","Count":1,"PinYin":"jining"},{"CityId":370900,"CityName":"泰安","Count":2,"PinYin":"taian"},{"CityId":371000,"CityName":"威海","Count":1,"PinYin":"weihai"},{"CityId":371100,"CityName":"日照","Count":1,"PinYin":"rizhao"},{"CityId":371200,"CityName":"莱芜","Count":1,"PinYin":"laiwu"},{"CityId":371300,"CityName":"临沂","Count":3,"PinYin":"linyi"},{"CityId":371400,"CityName":"德州","Count":1,"PinYin":"dezhou"},{"CityId":371500,"CityName":"聊城","Count":1,"PinYin":"liaocheng"},{"CityId":371600,"CityName":"滨州","Count":1,"PinYin":"binzhou"},{"CityId":371700,"CityName":"菏泽","Count":1,"PinYin":"heze"},{"CityId":410100,"CityName":"郑州","Count":5,"PinYin":"zhengzhou"},{"CityId":410300,"CityName":"洛阳","Count":1,"PinYin":"luoyang"},{"CityId":410400,"CityName":"平顶山","Count":1,"PinYin":"pingdingshan"},{"CityId":410500,"CityName":"安阳","Count":1,"PinYin":"anyang"},{"CityId":410700,"CityName":"新乡","Count":1,"PinYin":"xinxiang"},{"CityId":410800,"CityName":"焦作","Count":1,"PinYin":"jiaozuo"},{"CityId":410900,"CityName":"濮阳","Count":1,"PinYin":"puyang"},{"CityId":411000,"CityName":"许昌","Count":1,"PinYin":"xuchang"},{"CityId":411300,"CityName":"南阳","Count":1,"PinYin":"nanyang"},{"CityId":411400,"CityName":"商丘","Count":1,"PinYin":"shangqiu"},{"CityId":411500,"CityName":"信阳","Count":1,"PinYin":"xinyang"},{"CityId":411700,"CityName":"驻马店","Count":1,"PinYin":"zhumadian"},{"CityId":420100,"CityName":"武汉","Count":8,"PinYin":"wuhan"},{"CityId":420200,"CityName":"黄石","Count":1,"PinYin":"huangshi"},{"CityId":420300,"CityName":"十堰","Count":1,"PinYin":"shiyan"},{"CityId":420500,"CityName":"宜昌","Count":2,"PinYin":"yichang"},{"CityId":420600,"CityName":"襄阳","Count":1,"PinYin":"xiangyang"},{"CityId":420800,"CityName":"荆门","Count":1,"PinYin":"jingmen"},{"CityId":421000,"CityName":"荆州","Count":1,"PinYin":"jingzhou"},{"CityId":421100,"CityName":"黄冈","Count":1,"PinYin":"huanggang"},{"CityId":422800,"CityName":"恩施","Count":1,"PinYin":"enshi"},{"CityId":430100,"CityName":"长沙","Count":6,"PinYin":"changsha"},{"CityId":430200,"CityName":"株洲","Count":1,"PinYin":"zhuzhou"},{"CityId":430300,"CityName":"湘潭","Count":1,"PinYin":"xiangtan"},{"CityId":430400,"CityName":"衡阳","Count":1,"PinYin":"hengyang"},{"CityId":430500,"CityName":"邵阳","Count":1,"PinYin":"shaoyang"},{"CityId":430600,"CityName":"岳阳","Count":1,"PinYin":"yueyang"},{"CityId":430700,"CityName":"常德","Count":1,"PinYin":"changde"},{"CityId":431000,"CityName":"郴州","Count":1,"PinYin":"chenzhou"},{"CityId":431200,"CityName":"怀化","Count":1,"PinYin":"huaihua"},{"CityId":431300,"CityName":"娄底","Count":1,"PinYin":"loudi"},{"CityId":440100,"CityName":"广州","Count":12,"PinYin":"guangzhou"},{"CityId":440300,"CityName":"深圳","Count":13,"PinYin":"shenzhen"},{"CityId":440400,"CityName":"珠海","Count":2,"PinYin":"zhuhai"},{"CityId":440500,"CityName":"汕头","Count":1,"PinYin":"shantou"},{"CityId":440600,"CityName":"佛山","Count":4,"PinYin":"foshan"},{"CityId":440700,"CityName":"江门","Count":1,"PinYin":"jiangmen"},{"CityId":440800,"CityName":"湛江","Count":1,"PinYin":"zhanjiang"},{"CityId":441200,"CityName":"肇庆","Count":1,"PinYin":"zhaoqing"},{"CityId":441300,"CityName":"惠州","Count":1,"PinYin":"huizhou"},{"CityId":441400,"CityName":"梅州","Count":1,"PinYin":"meizhou"},{"CityId":441900,"CityName":"东莞","Count":6,"PinYin":"dongguan"},{"CityId":442000,"CityName":"中山","Count":2,"PinYin":"zhongshan"},{"CityId":445100,"CityName":"潮州","Count":1,"PinYin":"chaozhou"},{"CityId":445200,"CityName":"揭阳","Count":1,"PinYin":"jieyang"},{"CityId":450100,"CityName":"南宁","Count":4,"PinYin":"nanning"},{"CityId":450200,"CityName":"柳州","Count":1,"PinYin":"liuzhou"},{"CityId":450300,"CityName":"桂林","Count":1,"PinYin":"guilin"},{"CityId":460100,"CityName":"海口","Count":2,"PinYin":"haikou"},{"CityId":460200,"CityName":"三亚","Count":1,"PinYin":"sanya"},{"CityId":500100,"CityName":"重庆","Count":8,"PinYin":"chongqing"},{"CityId":510100,"CityName":"成都","Count":10,"PinYin":"chengdu"},{"CityId":510300,"CityName":"自贡","Count":1,"PinYin":"zigong"},{"CityId":510400,"CityName":"攀枝花","Count":1,"PinYin":"panzhihua"},{"CityId":510500,"CityName":"泸州","Count":1,"PinYin":"luzhou"},{"CityId":510600,"CityName":"德阳","Count":1,"PinYin":"deyang"},{"CityId":510700,"CityName":"绵阳","Count":1,"PinYin":"mianyang"},{"CityId":510900,"CityName":"遂宁","Count":1,"PinYin":"suining"},{"CityId":511100,"CityName":"乐山","Count":1,"PinYin":"leshan"},{"CityId":511300,"CityName":"南充","Count":1,"PinYin":"nanchong"},{"CityId":511400,"CityName":"眉山","Count":1,"PinYin":"meishan"},{"CityId":511500,"CityName":"宜宾","Count":1,"PinYin":"yibin"},{"CityId":511600,"CityName":"广安","Count":1,"PinYin":"guangan"},{"CityId":511700,"CityName":"达州","Count":1,"PinYin":"dazhou"},{"CityId":520100,"CityName":"贵阳","Count":4,"PinYin":"guiyang"},{"CityId":520200,"CityName":"六盘水","Count":1,"PinYin":"liupanshui"},{"CityId":520300,"CityName":"遵义","Count":1,"PinYin":"zunyi"},{"CityId":520400,"CityName":"安顺","Count":1,"PinYin":"anshun"},{"CityId":520500,"CityName":"毕节","Count":1,"PinYin":"bijie"},{"CityId":530100,"CityName":"昆明","Count":5,"PinYin":"kunming"},{"CityId":530300,"CityName":"曲靖","Count":1,"PinYin":"qujing"},{"CityId":530400,"CityName":"玉溪","Count":1,"PinYin":"yuxi"},{"CityId":532500,"CityName":"红河","Count":1,"PinYin":"honghe"},{"CityId":532900,"CityName":"大理","Count":1,"PinYin":"dali"},{"CityId":610100,"CityName":"西安","Count":7,"PinYin":"xian"},{"CityId":610300,"CityName":"宝鸡","Count":1,"PinYin":"baoji"},{"CityId":610400,"CityName":"咸阳","Count":1,"PinYin":"xianyang"},{"CityId":610500,"CityName":"渭南","Count":1,"PinYin":"weinan"},{"CityId":610600,"CityName":"延安","Count":1,"PinYin":"yanan"},{"CityId":610700,"CityName":"汉中","Count":1,"PinYin":"hanzhong"},{"CityId":610800,"CityName":"榆林","Count":1,"PinYin":"yulin"},{"CityId":620100,"CityName":"兰州","Count":4,"PinYin":"lanzhou"},{"CityId":620200,"CityName":"嘉峪关","Count":1,"PinYin":"jiayuguan"},{"CityId":620800,"CityName":"平凉","Count":1,"PinYin":"pingliang"},{"CityId":630100,"CityName":"西宁","Count":2,"PinYin":"xining"},{"CityId":640100,"CityName":"银川","Count":2,"PinYin":"yinchuan"},{"CityId":650100,"CityName":"乌鲁木齐","Count":2,"PinYin":"wulumuqi"}]
        city_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'cityname.txt'])
        cityname_list = []
        with open(city_file_path) as infile:
            for line in infile:
                cityname_list.append(line.strip())
        self.cityJsonData = []
        for cityinfo in self._cityJsonData:
            if cityinfo['CityName'] in cityname_list:
                self.cityJsonData.append(cityinfo)

    def init_url_generator(self, data, dmaps):
        brand_file_path = os.path.sep.join([self.cur_spider_dir, 'config', 'brandlist.txt'])
        brandl = []
        with open(brand_file_path) as infile:
            prefixs = 'https://car.autohome.com.cn/price/brand-'
            sufixs = '.html'
            for line in infile:
                brandl.append(line.strip().replace(prefixs,'').replace(sufixs,''))
        next_run_info = []
        for brandid in brandl:
            dmaps = {'%BRANDID%': brandid}
            tips = '<' + brandid + '> - page 1 '
            next_run_info.append((tips, self.sitename + '-brand', 'data_http', dmaps, 0))
        return next_run_info

    def brand_url_generator(self, data, dmaps):
        if data:
            html = lxml.html.fromstring(data)
            next_run_info = []
            #series run info
            brandid = dmaps['%BRANDID%']
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
                    next_run_info.append((tips, self.sitename + '-series', 'data_http', new_dmaps, 0))
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
                        next_run_info.append((tips1, self.sitename + '-dealer', 'data_http', new1_dmaps, 0))
                        #dealer price runinfo
                        new2_dmaps = copy.deepcopy(dealer_dmaps)
                        new2_dmaps['%CITYID%'] = cityid
                        next_run_info.append((tips2, self.sitename + '-price', 'data_http', new2_dmaps, 0))
            #next page run info
            next_page_xpath = '//div[@class="price-page"]//a[contains(@class,"page-item-next") and contains(@href,"/price/brand")]/@href'
            next_page_url = ''.join(html.xpath(next_page_xpath))
            if next_page_url:
                prefixs = 'https://car.autohome.com.cn/price/brand-'
                sufixs = '.html'
                next_page_url = 'https://car.autohome.com.cn' + next_page_url
                brandid = next_page_url.replace(prefixs,'').replace(sufixs,'')
                dmaps['%BRANDID%'] = brandid
                tips = '<' + brandid + '> - page 1 '
                next_run_info.append((tips, self.sitename + '-brand', 'data_http', dmaps, 0))
            if next_run_info:
                return next_run_info
        return None

    def convert_dealer_price_json(self, data, dmaps):
        prefixs = 'LoadDealerPrice('
        return json.loads(data.replace(prefixs,'')[:-1])

    def calc_today(self, dmaps):
        return str(datetime.date.today())

    def calc_brandid(self, dmaps, brandidinfo):
        prefixs = '/price/brand-'
        sufixs = '.html'
        return brandidinfo.replace(prefixs,'').replace(sufixs,'')

    def calc_seriesid(self, dmaps, seriesidinfo):
        #s1234, return 1234
        return seriesidinfo[1:]

    def calc_carcolorbg(self, dmaps, carcolorbginfo):
        return carcolorbginfo.replace('background:','').replace(';','').replace(' ','')

    def calc_specid(self, dmaps, specidinfo):
        return specidinfo[1:]

    def calc_seriesid_byurl(self, dmaps, seriesidurlinfo):
        prefixs = '//www.autohome.com.cn/'
        return seriesidurlinfo.replace(prefixs,'').split('/')[0]

    def calc_focusrank(self, dmaps, userfocusrankinfo):
        return userfocusrankinfo.replace('width:','')

    def calc_dealerid(self, dmaps, dealeridinfo):
        prefixs = '//dealer.autohome.com.cn/'
        return dealeridinfo.replace(prefixs,'').split('/')[0]