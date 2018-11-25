# -*- coding: utf-8 -*-
import os
import datetime
from sys import argv
from shutil import copyfile
import yaml
import pinyin

def copy_hanyu_data(filename = '{0:%Y-%m-%d}_hanzi.yaml'.format(datetime.datetime.today())):
    if os.path.exists(filename):
        data = yaml.load(open(filename))
        for wd in data:
            in_path = os.sep.join(['.','media',data[wd]['bishun']])
            out_path = os.sep.join(['.','ankimedia',wd+'.gif'])
            if os.path.exists(in_path) and not os.path.exists(out_path):
                copyfile(in_path, out_path)
            in_path = os.sep.join(['.','media',data[wd]['fayin']])
            out_path = os.sep.join(['.','ankimedia',wd+'.mp3'])
            if os.path.exists(in_path) and not os.path.exists(out_path):
                copyfile(in_path, out_path)
            print(wd, 'copied...')

def make_anki_card(filename = '{0:%Y-%m-%d}_hanzi.yaml'.format(datetime.datetime.today())):
    if os.path.exists(filename):
        data = yaml.load(open(filename))
        flash_card = []
        for wd in data:
            wd_info = data[wd]
            bishun = wd_info['bishun']
            fayin = wd_info['fayin']
            #flash card info
            front = wd
            back = '"{0}&nbsp;[sound:{1}]<div><img src={2}></div>"'.format(pinyin.get(wd), fayin, bishun)
            flash_card.append('\t'.join([front, back]))
        outfilename = '{0:%Y-%m-%d}_flashcard.txt'.format(datetime.datetime.today())
        with open(outfilename, 'w') as outf:
            for card in flash_card:
                outf.write(card)
                outf.write('\n')


if __name__=="__main__":
    if len(argv)==1:
        #copy_hanyu_data()
        make_anki_card()
    elif len(argv)==2:
        script, filename = argv
        #copy_hanyu_data(filename)
        make_anki_card(filename)
