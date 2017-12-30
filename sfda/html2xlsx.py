# -*- coding: utf-8 -*-
import os
from sys import argv
import lxml.html
from openpyxl import Workbook
from openpyxl.styles import Alignment


def read_product_html(prod_info_file_path):
    if os.path.exists(prod_info_file_path):
        infile = open(prod_info_file_path)
        return lxml.html.fromstring(infile.read())
    return None

def output_xpath_text(ws, cur_row, cur_col, html, xpath_expression):
    content_list = html.xpath(xpath_expression)
    if len(content_list)>0:
        ws.merge_cells(start_row=cur_row, start_column=cur_col, end_row=cur_row, end_column=cur_col+2)
        ws.cell(row=cur_row, column=cur_col, value=content_list[0].text)
        return cur_row+1
    return cur_row

def output_one_product_info(xlsxfilename, wb, cur_row, themonth, file_idx, prod_info_file_name):
    prod_info_file_path = '.' + os.sep + str(themonth) + os.sep + prod_info_file_name
    #creating worksheet
    ws = wb.active
    shname = 'J2017' + str(themonth)
    if 'heet' in ws.title:
        ws.title = shname
        wsidx = wb.create_sheet(shname + '_INDEX')
    else:
        ws = wb[shname] #.create_sheet(shname)
        wsidx = wb[shname + '_INDEX']
    wsidx.cell(row=file_idx+1, column=1, value=prod_info_file_name)
    fcell = wsidx.cell(row=file_idx+1, column=1)
    fcell.hyperlink = prod_info_file_path
    #wsidx.cell(row=file_idx+1, column=2, value=cur_row)
    fcell = wsidx.cell(row=file_idx+1, column=2)
    cvalue = str(cur_row)
    hlink = ''.join(['#', shname, '!A', cvalue])
    fcell.value = '=HYPERLINK("%s", "%s")' % (hlink, cvalue)
    #getting data
    xpath_title_zh = '//table[@class="pageEnd"]/tbody/tr[5]/td'
    xpath_title_py = '//table[@class="pageEnd"]/tbody/tr[6]/td'
    xpath_peifang = '//table[@class="pageEnd"]/tbody/tr[8]/td/table/tbody/tr[2]/td/table/tbody//tr'
    html = read_product_html(prod_info_file_path)
    if html is None:
        return cur_row
    #output titles
    cur_row = output_xpath_text(ws, cur_row, 1, html, xpath_title_zh)
    cur_row = output_xpath_text(ws, cur_row, 1, html, xpath_title_py)
    #output tables
    rows = html.xpath(xpath_peifang)
    merge_ind_list = [[0]*3 for i in range(len(rows))]
    def find_start_col(merge_ind_list_row, from_idx):
        for idx, x in enumerate(merge_ind_list_row):
            if idx<from_idx:
                continue
            if x==0:
                return idx
        return -1
    alcc = Alignment(horizontal="center", vertical="center")
    alvc = Alignment(vertical="center")
    alhc = Alignment(horizontal="center")
    for idx, rowhtml in enumerate(rows):
        cols = rowhtml.xpath('.//td')
        from_idx = 0
        for colhtml in cols:
            col_idx = find_start_col(merge_ind_list[idx], from_idx)
            first_cell = ws.cell(row=cur_row, column=col_idx+1)
            if idx==0 or col_idx==0:
                first_cell.alignment = alhc
            #mark rowspan information
            if 'rowspan' in colhtml.attrib:
                rowspan = int(colhtml.attrib['rowspan'])
                if rowspan>1:
                    for j in xrange(1,rowspan):
                        merge_ind_list[idx+j][col_idx] = 1
                    if col_idx==0:
                        first_cell.alignment = alcc
                    else:
                        first_cell.alignment = alvc
                    ws.merge_cells(start_row=cur_row, start_column=col_idx+1, end_row=cur_row+rowspan-1, end_column=col_idx+1)
            #output data
            ws.cell(row=cur_row, column=col_idx+1, value=colhtml.text)
            from_idx = col_idx + 1
        cur_row += 1
    cur_row += 1
    return cur_row
    #ws.cell(row=1, column=curcol, value=colname)
    #ws.merge_cells(start_row=1, start_column=curcol, end_row=2, end_column=curcol)

def main(themonth):
    flist = os.listdir('.' + os.sep + str(themonth))
    flist.sort()
    wb = Workbook()
    cur_row = 1
    flen = len(flist)
    xlsxfilename = str(themonth) + '.xlsx'
    for idx, f in enumerate(flist):
        cur_row = output_one_product_info(xlsxfilename, wb, cur_row, themonth, idx, f)
        print ' - %s  %d of %d' % (f, idx+1, flen)
    adjust_column_width(wb)
    wb.save(xlsxfilename)

def adjust_column_width(wb):
    for shname in wb.sheetnames:
        ws = wb[shname]
        if 'INDEX' in shname:
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 10
        else:
            ws.column_dimensions['A'].width = 10
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 20
        continue

        for col in ws.columns:
            max_length = 0
            column = col[0].column  # Get the column name
            for cell in col:
                if cell.row>1:
                    if cell.value:
                        if 'http' not in cell.value:
                            if isinstance(cell.value, unicode):
                                if len(cell.value)*1.2 > max_length:
                                    max_length = len(cell.value)*1.2
                            else:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                        else:
                            max_length = 10
            adjusted_width = (max_length + 2) * 1.2
            adjusted_width = adjusted_width if adjusted_width<60 else 60
            ws.column_dimensions[column].width = adjusted_width

if __name__=="__main__":
    script, themonth = argv
    main(themonth)