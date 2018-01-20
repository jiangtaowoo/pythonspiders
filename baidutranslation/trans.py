# -*- coding: UTF-8 -*-
import os
from sys import argv
import time
import json
import yaml
import codecs
from collections import deque
import copy
#import collections
#import urllib
#import lxml.html
import requests
from requests.models import Response as ReqResponse
import fanyi_sign
import gevent
from gevent import monkey
monkey.patch_all()

def time_decorator(method_to_be_timed):
    def timed(*args, **kw):
        ts = time.time()
        result = method_to_be_timed(*args, **kw)
        te = time.time()
        print 'func %s took %2.4fsec' % (method_to_be_timed.__name__, te-ts)
        return result
    return timed

class html_element_exists(object):
    def __init__(self, bywhat, id_or_name_or_xpath):
        self.bywhat = bywhat
        self.id_name_xpath = id_or_name_or_xpath

    def __call__(self, driver):
        from selenium.common.exceptions import NoSuchElementException
        try:
            if self.bywhat == 'id':
                element = driver.find_element_by_id(self.id_name_xpath)   # Finding the referenced element
            elif self.bywhat == 'name':
                element = driver.find_element_by_name(self.id_name_xpath)   # Finding the referenced element
            elif self.bywhat == 'xpath':
                element = driver.find_element_by_xpath(self.id_name_xpath)   # Finding the referenced element
            else:
                return False
        except NoSuchElementException:
            return False
        return element
    

class BDTranslation(object):
    def __init__(self):
        self.js_var_dict = dict()
        self.request_dict = dict()
        self._session = requests.session()
        self.words_tobe_t = deque([])
        self.tran_results = dict()

    def _init_request(self):
        cookie_dict = {'locale': 'zh', 'BAIDUID': '84714D78F6D00E5CF202E62D0D643143:FG=1'}
        self._session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        url = 'http://fanyi.baidu.com'
        headers = {'Host': 'fanyi.baidu.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Connection': 'keep-alive', 'Referer': 'http://fanyi.baidu.com/', 'X-Requested-With': 'XMLHttpRequest'}
        self.request_dict['url'] = url
        self.request_dict['headers'] = headers
        rsp = self._session.get(**self.request_dict)
        return self._get_js_var(rsp)

    def _get_js_var(self, rsp):
        if isinstance(rsp, ReqResponse):
            htmlText = rsp.text
        else:
            htmlText = rsp
        try:
            idx1 = htmlText.index('window.gtk')
            window_gtk = str(htmlText[idx1:idx1+50].split(';')[0].split('=')[1].strip().replace("'",''))
            idx2 = htmlText.index('token:')
            token = str(htmlText[idx2:idx2+50].split(',')[0].split(':')[1].strip().replace("'",""))
            self.js_var_dict['token'] = str(token)
            self.js_var_dict['gtk'] = str(window_gtk)
            return True
        except:
            return None

    def _gen_payload(self, word, srclang):
        token = self.js_var_dict['token']
        window_gtk = self.js_var_dict['gtk']
        sign = fanyi_sign.calc_sign(word, window_gtk)
        payload = dict()#collections.OrderedDict()
        payload['from'] = srclang
        payload['to'] = 'en' if srclang=='zh' else 'zh'
        payload['query'] = word
        payload['simple_means_flag'] = '3'
        payload['sign'] = sign
        payload['token'] = token
        #payload['query'] = urllib.quote(word.encode('utf-8'))
        return payload

    def _load_words(self, filename):
        #return yaml.load(open(filename))['words']
        if os.path.exists(filename):
            words = []
            self.words_tobe_t = deque([])
            lineidx = 0
            with codecs.open(filename, 'r', 'utf-8') as infile:
                for line in infile:
                    line = line.replace('\r','').replace('\n','').strip()
                    if line:
                        self.words_tobe_t.append((lineidx,line))
                        words.append(line)
                        lineidx += 1
            return words
            #data = yaml.load(open(filename))
            #if not isinstance(data, list):
            #    data = data.split(' ')
            #return data
        return False

    def _parse_trans_rsp(self, rsp):
        if isinstance(rsp, ReqResponse):
            try:
                return json.loads(rsp.text)['trans_result']['data'][0]['dst']
            except:
                return None
        return None

    def _output_trans_results(self, words, tran_results):
        print len(words), len(tran_results)
        return True
        for word in words:
            print word, tran_results[word]

    def _output_trans_results_tofile(self, words, tran_results, filename='trans_result.txt'):
        with codecs.open(filename, 'w', 'utf-8') as outf:
            for word in words:
                if isinstance(tran_results[word], str) or isinstance(tran_results[word], unicode):
                    outf.write(word)
                    outf.write('\n')
                    outf.write(tran_results[word])
                    outf.write('\n')
                else:
                    print word, type(tran_results[word])

    def translate_worker(self, workerid, srclang):
        while self.words_tobe_t:
            lineidx, word = self.words_tobe_t.popleft()
            if word:
                print 'Woker %d is traslating line %d ...' % (workerid, lineidx)
                req_dict = copy.deepcopy(self.request_dict)
                req_dict['data'] = self._gen_payload(word, srclang)
                rsp = self._session.post(**req_dict)
                dst_word = self._parse_trans_rsp(rsp)
                if dst_word is None:
                    self.words_tobe_t.append((lineidx, word))
                    print '****** Worker %d failed on line %d ...' % (workerid, lineidx)
                    gevent.sleep(5)
                else:
                    self.tran_results[word] = dst_word
            else:
                gevent.sleep(0)
        print 'worker %d is quiting ...' % (workerid)

    def translate_request(self, srclang='zh', filename='wordlist.txt'):
        # srclang='zh'   translate   zh --> en
        # srclang='en'   translate   en --> zh
        words = self._load_words(filename)
        urlapi = 'http://fanyi.baidu.com/v2transapi'
        #step 1. first visit, to get gtk, token
        if not self._init_request():
            print 'init failed, quiting'
            return False
        #step 2. visit translate api
        tran_results = dict()
        self.request_dict['url'] = urlapi
        # start gevent thread
        threads = []
        c_worker_size = 20
        for i in xrange(0,c_worker_size):
            threads.append( gevent.spawn(self.translate_worker, i+1, srclang) )
        gevent.joinall( threads )
        """
        for idx, word in enumerate(words):
            self.request_dict['data'] = self._gen_payload(word, srclang)
            rsp = self._session.post(**self.request_dict)
            tran_results[word] = self._parse_trans_rsp(rsp)
            print 'transalting %d of %d' % (idx, len(words))
            #break
        """
        print 'saving result ...'
        self._output_trans_results_tofile(words, self.tran_results)
        #self._output_trans_results(words, self.tran_results)

    def translate_selenium(self, srclang='zh', filename='wordlist.txt'):
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        url = 'https://fanyi.baidu.com'
        urlbase = 'https://fanyi.baidu.com/#zh/en/'
        words = self._load_words(filename)
        dr = webdriver.Firefox()
        dr.get(url)
        tran_results = dict()
        result_xpath = '//p[contains(@class,"target-output")]/span'
        for word in words:
            dr.get( urlbase + word )
            elem = WebDriverWait(dr, 60).until(html_element_exists('xpath', result_xpath))
            tran_results[word] = elem.text
            dr.get(url)
        dr.quit()
        self._output_trans_results(words, tran_results)

    @time_decorator
    def translate(self, srclang='zh', filename='wordlist.txt', visible=False):
        if not visible:
            self.translate_request(srclang, filename)
        else:
            self.translate_selenium(srclang, filename)

if __name__=="__main__":
    tranobj = BDTranslation()
    if len(argv)==1:
        tranobj.translate()
    elif len(argv)==3:
        script, lang, filename = argv
        if lang in ['en','zh'] and os.path.exists(filename):
            tranobj.translate(srclang=lang, filename=filename)