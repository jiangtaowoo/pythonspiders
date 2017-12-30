# -*- coding: utf-8 -*-
import os

def get_no_product_details_info(themonth):
    themonth = str(themonth)
    log_file_name = 'sfda_trace_' + themonth + '.log'
    log_no_prod_file_name = 'sfda_nodetails_' + themonth + '.log'
    prod_dict = dict()
    with open(log_file_name) as infile:
        for line in infile:
            line = line.strip().split('\t')
            if 'No product details' in line[3]:
                if line[1] not in prod_dict:
                    prod_dict[line[1]] = (line[2], line[3])
    with open(log_no_prod_file_name, 'w') as outf:
        for k, v in prod_dict.iteritems():
            line = '\t'.join([k, v[0], v[1]])
            outf.write(line)
            outf.write('\n')

def main():
    for i in xrange(0,10):
        get_no_product_details_info(i)

if __name__=="__main__":
    main()