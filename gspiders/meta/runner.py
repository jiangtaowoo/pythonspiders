# -*- coding: utf-8 -*-
import copy
import hashlib
from meta.setting import ConfigManager

class Runner(object):
    _MAX_RETRY = 5

    def __init__(self, siteid, refdict, prompt_msg=''):
        #基础信息
        self._site_id = ''
        #所有信息
        self._cfgs = None
        #Request信息
        self._reqs = None
        #控制信息
        self._ctls = None
        #Pass throught信息
        self._pass_through = None
        #retry
        self._retry = 0
        #prompt
        self._prompt_msg = ''
        self.make_runner(siteid, refdict, prompt_msg)
        #md5
        self._md5 = self._calc_md5()


    @staticmethod
    def _iter_map_str(obj, refdict):
        if isinstance(obj, str) or isinstance(obj, unicode):
            newobj = obj
            for k in refdict:
                if k in newobj:
                    if not isinstance(refdict[k], str) or isinstance(refdict[k], unicode):
                        newobj = newobj.replace(k, str(refdict[k]))
                    else:
                        newobj = newobj.replace(k, refdict[k])
        elif isinstance(obj, list):
            newobj = []
            for o in obj:
                newobj.append(Runner._iter_map_str(o, refdict))
        elif isinstance(obj, dict):
            newobj = dict()
            for k in obj:
                newobj[k] = Runner._iter_map_str(obj[k], refdict)
        else:
            newobj = obj
        return newobj

    @staticmethod
    def _no_iter_data(data, key):
        return data[key] if key in data else None

    @staticmethod
    def _iter_data(key, data):
        if key in data:
            return data[key]
        if isinstance(data, dict):
            for k in data:
                ret = Runner._iter_data(key, data[k])
                if ret:
                    return ret
            return None
        else:
            return None

    @property
    def id(self):
        return self._site_id

    @property
    def md5(self):
        if not self._md5:
            self._md5 = self._calc_md5()
        return self._md5

    def _calc_md5(self):
        m = hashlib.md5(''.join([self._site_id,
                                 json.dumps(self._pass_through)]))
        return m.hexdigest()

    def make_runner(self, siteid, refdict, prompt_msg=''):
        confm = ConfigManager()
        _http_cfgs = confm.get_spider_config(confm.spidername)['http']
        self._site_id = siteid
        self._pass_through = copy.deepcopy(refdict)
        self._cfgs = Runner._iter_map_str(_http_cfgs[siteid], refdict)
        self._reqs = self._cfgs['request']
        self._ctls = self._cfgs['control']
        self._prompt_msg = prompt_msg

    def has_retry_opportunity(self):
        self._retry += 1
        if self._retry<Runner._MAX_RETRY:
            return True
        return False

    def is_selenium_noparam_proc(self, funcname):
        if funcname=='send_keys':
            return False
        return True

    def get_request_method(self):
        return Runner._no_iter_data(self._reqs, 'method')

    def get_reqeust_kwargs(self):
        return Runner._no_iter_data(self._reqs, 'kwargs')

    def get_url(self):
        return Runner._no_iter_data(self._reqs['kwargs'], 'url')

    def get_loginid(self):
        return Runner._no_iter_data(self._ctls, 'loginid')

    def get_proxy(self):
        return Runner._no_iter_data(self._ctls, 'proxy')

    def get_sleep(self):
        return Runner._no_iter_data(self._ctls, 'sleep')

    def get_selenium_locate(self):
        return Runner._no_iter_data(self._ctls, 'locate')

    def get_data_viakey(self, key):
        return Runner._iter_data(key, self._reqs) or Runner._iter_data(key, self._pass_through)

    def get_prompt_msg(self):
        return self._prompt_msg

