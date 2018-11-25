# -*- coding: utf-8 -*-
import os
from sys import argv
import time
import datetime
import json
import yaml
import lxml.html
from lxml import etree
from collections import deque
import copy
import requests
from requests.models import Response as ReqResponse
import traceback
#import gevent
#from gevent import monkey
#monkey.patch_all()

def time_decorator(method_to_be_timed):
    def timed(*args, **kw):
        ts = time.time()
        result = method_to_be_timed(*args, **kw)
        te = time.time()
        print('func %s took %2.4fsec' % (method_to_be_timed.__name__, te-ts))
        return result
    return timed


class BDTranslation(object):
    def __init__(self):
        self._cookie_set = False
        self.request_dict = dict()
        self._session = requests.session()
        self.words_tobe_t = deque([])
        self.tran_results = dict()

    def _init_request(self):
        if not self._cookie_set:
            cookie_dict = {'locale': 'zh', 'BAIDUID': '84714D78F6D00E5CF202E62D0D643143:FG=1'}
            self._session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
            url = 'http://hanyu.baidu.com'
            headers = {'Host': 'hanyu.baidu.com', 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Connection': 'keep-alive', 'Referer': 'http://hanyu.baidu.com/', 'X-Requested-With': 'XMLHttpRequest'}
            self.request_dict['url'] = url
            self.request_dict['headers'] = headers
            rsp = self._session.get(**self.request_dict)
            if rsp.status_code==200:
                self._cookie_set = True
        return self._cookie_set

    def _load_words(self, filename):
        if os.path.exists(filename):
            wd_list = yaml.load(open(filename))
            words = []
            self.words_tobe_t = deque([])
            lineidx = 0
            for wd in wd_list:
                self.words_tobe_t.append((lineidx,wd))
                words.append(wd)
                lineidx += 1
            return words
        return False

    def _parse_trans_rsp(self, rsp):
        def _stringify_node(node):
            parts = ([x for x in node.itertext()])
            return ''.join(filter(None, parts)).strip()
        if isinstance(rsp, ReqResponse) and rsp.status_code==200:
            pinyin_data = {}
            try:
                xml_data = lxml.html.fromstring(rsp.text)
                #step 1. 获取汉语拼音
                xpath_pinyin = "//div[@id='pinyin']/span/b"
                pinyin_divs = xml_data.xpath(xpath_pinyin)
                if pinyin_divs:
                    pinyin_data['pinyin'] = _stringify_node(pinyin_divs[0])
                #step2. 获取笔顺, 发音
                xpath_bishun = '//img[@id="word_bishun"]'
                xpath_fayin = "//div[@id='pinyin']/span/a"
                paths = {'bishun': xpath_bishun, 'fayin': xpath_fayin}
                for k in paths:
                    divs = xml_data.xpath(paths[k])
                    if divs:
                        if k=='bishun':
                            suffix = 'gif'
                        else:
                            suffix = 'mp3'
                        for kk in divs[0].attrib:
                            kv = divs[0].attrib[kk]
                            if len(kv)>3 and kv[-3:]==suffix:
                                url = kv
                                break
                        #url = _stringify_node(divs[0])
                        req_dict = copy.deepcopy(self.request_dict)
                        req_dict['url'] = url
                        req_dict['headers']['Host'] = 'appcdn.fanyi.baidu.com'
                        req_dict['headers']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                        raw_filename = url.split('/')[-1]
                        pinyin_data[k] = raw_filename
                        today_str = '{0:%Y-%m-%d}'.format(datetime.datetime.today())
                        media_subpath = os.sep.join(['.','media',today_str])
                        if not os.path.exists(media_subpath):
                            print(media_subpath)
                            os.makedirs(media_subpath)
                        raw_filepath = os.sep.join([media_subpath,raw_filename])
                        if not os.path.exists(raw_filepath):
                            sub_rsp = self._session.get(**req_dict)
                            if sub_rsp.status_code==200:
                                with open(raw_filepath, 'wb') as outf:
                                    outf.write(sub_rsp.content)
                            else:
                                print('fetch {0} error, stauts_code={1}!'.format(raw_filename, sub_rsp.status_code))
                return pinyin_data
            except Exception as e:
                print("Exception!!! type error: " + str(e))
                print(traceback.format_exc())
                return None
        return None

    def _output_trans_results(self, words, tran_results):
        print(len(words), len(tran_results))
        return True
        for word in words:
            print(word, tran_results[word])

    def _output_trans_results_tofile(self, words, tran_results, filename='{0:%Y-%m-%d}_hanzi.yaml'.format(datetime.datetime.today())):
        with open(filename, 'w') as outf:
            yaml.dump(tran_results, outf)

    def translate_worker(self, workerid):
        while self.words_tobe_t:
            lineidx, word = self.words_tobe_t.popleft()
            if word:
                print('Woker %d is working on line %d: %s ...' % (workerid, lineidx, word))
                req_dict = copy.deepcopy(self.request_dict)
                req_dict['params'] = {'ptype': 'zici', 'tn': 'sug_click', 'wd': word}
                rsp = self._session.get(**req_dict)
                pinyin_data = self._parse_trans_rsp(rsp)
                if pinyin_data is None:
                    #self.words_tobe_t.append((lineidx, word))
                    print('****** Worker %d failed on line %d: %s ...' % (workerid, lineidx, word))
                    #gevent.sleep(5)
                else:
                    self.tran_results[word] = pinyin_data
            else:
                pass
                #gevent.sleep(0)
        print('worker %d is quiting ...' % (workerid))

    def make_request(self, filename='words.yaml'):
        words = self._load_words(filename)
        urlword = 'https://hanyu.baidu.com/s'
        #step 1. first visit, set cookie
        if not self._init_request():
            print('init failed, quiting')
            return False
        #step 2. visit url
        tran_results = dict()
        self.request_dict['url'] = urlword
        # start gevent thread
        self.translate_worker(1)
        """
        threads = []
        c_worker_size = 1
        for i in xrange(0,c_worker_size):
            threads.append( gevent.spawn(self.translate_worker, i+1) )
        gevent.joinall( threads )
        """
        print('saving result ...')
        self._output_trans_results_tofile(words, self.tran_results)
        #self._output_trans_results(words, self.tran_results)

    @time_decorator
    def translate(self, filename='words.yaml'):
        self.make_request(filename)

if __name__=="__main__":
    tranobj = BDTranslation()
    if len(argv)==1:
        tranobj.translate()
    elif len(argv)==2:
        script, filename = argv
        tranobj.translate(filename=filename)
