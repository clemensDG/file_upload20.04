#coding:utf8

import xlrd
import datetime
import pickle,os,sys
from lxml import etree
import json

EXCEL_RULE={
    u"FSU运维ID":"fsuid",
    u"经度":"ns",
    u"纬度":"we",
    u"无线模块型号":"nmvendor",
    u"IMSI卡号":"ImsiId",
    u"站址运维ID":"addr",
    #u"网络制式":"NetworkType",

}

update_list=[]

def dump_fsu_config(fsu_dict):
    with open("/home/fsu_env/fsu_config.pkl","wb+") as pkfile:
        pickle.dump(fsu_dict,pkfile)
        pkfile.close()

def load_fsu_config():
    try:
        with open("/home/fsu_env/fsu_config.pkl","rb") as pkfile:
            fsu_dict= pickle.load(pkfile)
            pkfile.close()
    except:
        fsu_dict={}
    return fsu_dict

def load_fsu_list(file_path):
    """
    load 用户数据
    :param file_path:
    :return:
    """
    NAME_LIST=[] #使用的excel员工表的列名
    INDEX_LIST=[] #使用的excel员工表的序号index
    user_book=xlrd.open_workbook(file_path) #打开excel
    sh_data=user_book.sheet_by_index(0)  #打开第一章sheet
    USER_NAME_CEL=0
    update_list=[]
    #print sh_data.nrows  #总行数
    #print sh_data.ncols #总列数

    #获取存在于EXCEL_RULE 的列
    for index,cel_name in enumerate(sh_data.row_values(0)):
        if cel_name in EXCEL_RULE.keys():
            #print index,cel_name

            NAME_LIST.append(cel_name)
            INDEX_LIST.append(index)
    #print NAME_LIST,INDEX_LIST


    fsu_dict=load_fsu_config()
    for row_num in range(1,sh_data.nrows):   #获取数据
        row_data=sh_data.row_values(row_num) #每行数据
        #print row_data
        # user_obj = employee()  #初始对象
        #df_fsu_id="00000000000000"
        each_fsu={}
        for feild_index,index in enumerate(INDEX_LIST):
            each_fsu[EXCEL_RULE[NAME_LIST[feild_index]]]=row_data[index]
        each_fsu["fsucode"]=each_fsu["fsuid"]
        update_list.append(each_fsu["fsuid"])
        fsu_dict[each_fsu["fsuid"]]=each_fsu
    dump_fsu_config(fsu_dict)
    return update_list


def load_fsu_device(floder_path,add_list=[],NOT_KT=False):
    fsu_dict=load_fsu_config()
    #print fsu_dict
    #print fsu_dict.keys()
    #file_path_list=[]
    update_list = []
    for path, d, filelist in os.walk(floder_path):
        #print filelist
         for filename in filelist:
        #     file_path_list.append(os.path.join(path, filename))
            device_book = xlrd.open_workbook(os.path.join(path, filename))  # 打开excel
            sh_data = device_book.sheet_by_index(0)  # 打开第一章sheet
            fsu_id=sh_data.cell(4,2).value
            #print "fsu_id",fsu_id,filename
            if fsu_id not in fsu_dict.keys():
                continue
            if fsu_id not in add_list:
                continue
            update_list.append(fsu_id)
            device_list=[]
            for row_num in range(4, sh_data.nrows):
                #屏蔽空调 待加
                #print "##############", sh_data.cell(row_num, 2).value
                dtype = sh_data.cell(row_num,2).value[7:9]
                if dtype == "15" and NOT_KT:

                    continue
                device_list.append( sh_data.cell(row_num,2).value)
            fsu_dict[fsu_id]["device_list"]=device_list
    dump_fsu_config(fsu_dict)
    return update_list

def chang_device_resp(fsuid,Id, val):
    '''
    格式化xml请求，输出一个字典
    :param content_: xml请求文本
    :return: 修改后的字典
    '''
    device_type = Id[2:4]
    device_resp = {}
    jsonPath = '/home/file_upload/json/device_resp_base_%s.json'%(fsuid)
    if os.path.exists(jsonPath):
        rf = open(jsonPath, 'r')
    else:
        rf = open('/home/file_upload/device_resp.json', 'r')
    device_resp = json.load(rf)
    device_code_val = device_resp[device_type]
    device_xml = etree.XML(device_code_val)
    tree = device_xml.xpath("//TSemaphore")
    for TS_node in tree:
        if TS_node.attrib.get('Id')==Id:
            TS_node.attrib['MeasuredVal'] = val
    content = etree.tounicode(device_xml)
    device_resp[device_type] = content
    tf = open('/home/file_upload/json/device_resp_base_%s.json'%(fsuid),'w')
    json.dump(device_resp,tf)
    tf.close()




#if __name__=="__main__":
    # try:
    #
    #     arg_check=sys.argv[1]
    #     if arg_check.lower()=="nkt":
    #         NOT_KT = True
    #     else:
    #         NOT_KT=False
    #
    # except:
    #     NOT_KT=False
    #
    # print NOT_KT

    # timestr=datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")
    # fsu_new_name="fsu_config_%s.pkl" %(timestr)
    # os.popen("cp fsu_config.pkl %s" %(fsu_new_name))
    # #load_fsu_list("./excel_fsu_list/all_fsu_list.xls")
    #
    #
    # load_fsu_list("./excel_fsu_list/update_fsu_list.xls")
    # with open("./update_fsu_list","wb") as update_fsu_file:
    #     update_fsu_file.write("\n".join(update_list))
    #     update_fsu_file.close()

    # load_fsu_device("./excel_fsu_list/device/")
    # if update_list:
    #     print u"更新失败！请确认关联设备",update_list
    #     os.popen("cp %s fsu_config.pkl" %(fsu_new_name))
    # else:
    #     print u"更新成功!"


