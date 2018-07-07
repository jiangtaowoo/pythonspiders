# -*- coding: utf-8 -*-
from dto.dtomanager import DTOManager

"""
Paser Base Class, when we create a new spider
we should create a new DiyParser and derive from Parser
the following 5 method must be implemented:
1. init_runners
2. is_response_success      to call extract_data or error_handler
3. handle_response_error
4. clean_response_data
5. generate_more_page   to generate more page for crawler

the main process for parser is implemented by
parse(Response) function
"""
class Parser(object):
    def __init__(self):
        pass

    def dispatch_response(self, runner, rsp):
        try:
            if self.is_response_success(runner, rsp):
                dto = DTOManager()
                #1. clean response data
                data = self.clean_response_data(runner, rsp)
                #2. extract data
                dataset = dto.extract_data(runner, data)
                #3. generate redirect page (当前页数据, 可以携带到下一个请求中)
                runners = self.generate_more_page(runner, rsp, dataset)
                #4. data saver modules
                models = dto.get_data_models(runner)
                #5. return data
                return True, (runners, models, dataset)
            else:
                errs = self.handle_response_error(runner, rsp)
                return False, errs
        except Exception, errs:
            return False, unicode(errs)


    """
    the following functions should be override in derived class
    """
    def init_runners(self):
        return None

    def is_response_success(self, runner, rsp):
        return True

    def handle_response_error(self, runner, rsp):
        return None

    def generate_more_page(self, runner, rsp, dataset):
        return None

    def clean_response_data(self, runner, rsp):
        return rsp

    """
    other callback diy functions
    """
