# -*- coding: utf-8 -*-
import os
from sys import argv
import yaml
from jinja2 import Environment, PackageLoader, FileSystemLoader, select_autoescape


def get_spider_folder(spidername):
    cur_app_dir = os.path.dirname(os.path.abspath(__file__))
    spider_folder = os.path.sep.join([cur_app_dir, spidername])
    return spider_folder

def init_spider_info(spidername):
    spider_folder = get_spider_folder(spidername)
    spider_info_file = os.path.sep.join([spider_folder, 'siteinfo.txt'])
    if not os.path.exists(spider_folder):
        os.makedirs(spider_folder)
    flist = []
    with open(spider_info_file) as infile:
        for line in infile:
            flist.append(line.strip().split('|'))
    return flist

def read_module_info(spidername):
    spider_folder = get_spider_folder(spidername)
    file_path = os.path.sep.join( [spider_folder, 'models.yaml'] )
    mdict = yaml.load(open(file_path))
    modinfos = dict()
    for modname, modinfo in mdict.iteritems():
        modinfos[modname] = dict()
        modinfos[modname]['cols'] = []
        for fname, fneed in modinfo['cols'].iteritems():
            modinfos[modname]['cols'].append(fname)
    return modinfos

def read_dtocb_info(spidername):
    spider_folder = get_spider_folder(spidername)
    spider_dtomap_file = os.path.sep.join([spider_folder, 'dtomap.yaml'])
    if os.path.exists(spider_dtomap_file):
        cbinfos = dict()
        sitecb_names = dict()
        dtodict = yaml.load(open(spider_dtomap_file))
        for sitehttp, sitecfg in dtodict.iteritems():
            if 'callback' in sitecfg and 'classinfo' in sitecfg['callback'] and 'modulename' in sitecfg['callback']['classinfo']:
                pkg_name = sitecfg['callback']['classinfo']['modulename']
                if pkg_name:
                    if pkg_name not in cbinfos:
                        cbinfos[pkg_name] = dict()
                    if pkg_name not in sitecb_names:
                        sitecb_names[pkg_name] = dict()
                    cls_name = sitecfg['callback']['classinfo']['classname']
                    if not cls_name:
                        cls_name = 'UNDEFINED_CLS_NAME'
                    if 'col_calc' in sitecfg:
                        #sitename info
                        if cls_name not in sitecb_names[pkg_name]:
                            sitecb_names[pkg_name][cls_name] = [sitehttp]
                        else:
                            if sitehttp not in sitecb_names[pkg_name][cls_name]:
                                sitecb_names[pkg_name][cls_name].append(sitehttp)
                        #callback function info
                        if cls_name not in cbinfos[pkg_name]:
                            cbinfos[pkg_name][cls_name] = dict()
                        for colid, colfuncs in sitecfg['col_calc'].iteritems():
                            if colfuncs[0] not in cbinfos[pkg_name][cls_name]:
                                cbinfos[pkg_name][cls_name][colfuncs[0]] = colfuncs[1:]
                    #print cbinfos
        return cbinfos, sitecb_names
    return None, None

def generate_spider_template(env, input_datas, datakeylist, templ_file_name, outdict, out_file_name=None):
    template = env.get_template(templ_file_name)
    render_kw = dict()
    for datakey in datakeylist:
        render_kw[datakey] = input_datas[datakey]
    outdata = template.render(**render_kw)
    if not out_file_name:
        out_file_name = templ_file_name
    outdict[out_file_name] = outdata

def output_spider_template(spidername, outdict):
    spider_folder = get_spider_folder(spidername)
    for fname, fval in outdict.iteritems():
        file_path = os.path.sep.join([spider_folder, fname])
        with open(file_path, 'w') as outf:
            outf.write(fval)

if __name__=="__main__":
    template_dir = os.path.sep.join( [os.path.dirname(os.path.abspath(__file__)), 'templates'] )
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=False)

    spidername = argv[1]
    input_datas = dict()
    outdict = dict()
    sites = init_spider_info(spidername)
    input_datas['JJ2_sites'] = sites
    modinfos = read_module_info(spidername)
    input_datas['JJ2_modinfos'] = modinfos
    cbinfos, sitecb_names = read_dtocb_info(spidername)

    if len(argv)==2:
        script, spidername = argv
        generate_spider_template(env, input_datas, ['JJ2_sites'], 'tenants.yaml', outdict)
        generate_spider_template(env, input_datas, ['JJ2_sites'], 'http.yaml', outdict)
        generate_spider_template(env, input_datas, ['JJ2_sites', 'JJ2_modinfos'], 'dtomap.yaml', outdict, out_file_name='dtomap_.yaml')
    elif len(argv)==3:
        script, spidername, dtomap = argv
        for pkg_name, pkg_info in cbinfos.iteritems():
            input_datas['JJ2_sitecbs'] = pkg_info
            input_datas['JJ2_sitecbnames'] = sitecb_names[pkg_name]
            generate_spider_template(env, input_datas, ['JJ2_sites', 'JJ2_sitecbs', 'JJ2_sitecbnames'], 'callback.py', outdict, out_file_name=pkg_name+'.py')
    if outdict:
        output_spider_template(spidername, outdict)
