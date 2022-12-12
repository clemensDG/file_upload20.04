import docker
import subprocess
import json
from lxml import etree
import random
from datetime import datetime
import os



def batch_updata_resp(fsu_id):
    # up_val ={"0406101001": "223.70","0406102001": "220.90","0406103001": "220.10","0406111001": "53.20","0406112001":"43.17"}
    up_list = ["0406101001","0406102001","0406103001","0406111001","0406112001"]
    # print('./json/device_resp_%s.json'%(fsu_id)) 
    device_rsp = {}
    jsonPath = '/home/file_upload/json/device_resp_base_%s.json'%(fsu_id)
    if os.path.exists(jsonPath):
        rf = open(jsonPath, 'r')
    else:
        commandcp = 'cp /home/file_upload/device_resp.json '+jsonPath
        subprocess.call(commandcp, shell=True)
        rf = open('/home/file_upload/device_resp.json', 'r')
    device_resp = json.load(rf)
    device_code_val = device_resp['06']
    #print(device_code_val)
    device_xml = etree.XML(device_code_val)
    tree = device_xml.xpath("//TSemaphore")
    # up_val = {}
    # print(tree)
    for id in up_list:
        for TS_node in tree:
            if TS_node.attrib.get('Id') == id:
                val = ''
                if id == "0406111001":
                    val = str(round(random.uniform(51.97,55.02),2))
                elif id == "0406112001":
                    I_val_base = float(TS_node.attrib.get('MeasuredVal'))
                    if datetime.hour == 22:
                        I_val = I_val_base-1
                    elif datetime.hour == 6:
                        I_val = I_val_base+1
                    else:
                        I_val = I_val_base
                    val = str(round(random.uniform(I_val-1,I_val+1),2))
                else:
                    val = str(round(random.uniform(210.21,238.17),2))
                TS_node.attrib['MeasuredVal'] = val 
                # print(id,val)
                content = etree.tounicode(device_xml)
                device_resp['06'] = content
    tf = open('/home/file_upload/json/device_resp_%s.json'%(fsu_id), 'w')
    json.dump(device_resp,tf)
    tf.close()


client = docker .from_env()
docker_ps_list = client.containers.list()
# result = client.version()
# print(result)
name_list = []
for container in docker_ps_list: 
    con_name = container.attrs.get('Name').replace('/','')
    if len(con_name)>13:
        fsu_id = con_name
        # commandcpl = 'cp /home/file_upload/json/device_resp_%s.json /home/file_upload/json/device_resp_base_%s.json'%(fsu_id,fsu_id)
        #print(commandcpl)
        #subprocess.call(commandcpl, shell=True)
        batch_updata_resp(fsu_id) 
        command = 'docker cp json/device_resp_%s.json %s:/usr/local/device_resp.json'%(fsu_id,fsu_id)
        print(command)
    #command1 = 'docker restart %s'%(name)
    #print(command1)
        subprocess.call(command, shell=True)
Date = datetime.now()
print(Date,': autochange over!!!')
    #command = 'cp device_resp.json json/device_resp_%s.json'%(name)
    #print(command)
    #subprocess.call(command, shell=True)
    # print('docker cp %s:/usr/local/device_resp.json json/device_resp_%s.json'%(name,name))
#command = 'docker cp 14098143800511:/usr/local/device_resp.json json/device_resp_14098143800511.json'
#pop = subprocess.Popen(command, shell=True)
#out = pop.stderr.read()
#print(out)
