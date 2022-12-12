# coding:utf8
import os
import time
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from update_fsu_config import load_fsu_list, load_fsu_device, load_fsu_config, chang_device_resp
import datetime
import shutil
import subprocess, os, sys

# FSU列表放置路径
UPLOAD_FOLDER_LIST = '/home/excel_fsu_list/'
# FSU关联设备放置路径
UPLOAD_FOLDER_DEVICE = '/home/excel_fsu_list/device/'

ALLOWED_EXTENSIONS = set(['xls'])  # 允许上传的文件格式

#
FSU_DICT_FILE = "/home/fsu_env/fsu_config.pkl"
FSU_DICT_PATH = "/home/fsu_env/"

app = Flask(__name__)
app.config['UPLOAD_FOLDER_LIST'] = UPLOAD_FOLDER_LIST
app.config['UPLOAD_FOLDER_DEVICE'] = UPLOAD_FOLDER_DEVICE

############log#############
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('/var/run/fsu_config_manager.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)


############################




def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/", methods=['GET'])
def index():
    return u"""
    <!doctype html>
    <title>FSU配置更新管理</title>
    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>
    """


@app.route("/list", methods=['GET', 'POST'])
def list():
    if request.method == 'POST':
        logger.info(u">>上传fsu列表,upload_list")
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER_LIST'], filename))
            return redirect(url_for('list'))
    return u"""
    <!doctype html>
    <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

    <h1>FSU列表上传</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=上传>
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER_LIST'], ))


@app.route("/device", methods=['GET', 'POST'])
def device():
    if request.method == 'POST':
        logger.info(u">>上传关联设备,upload_device")
        # uploaded_files = request.files['file[]']
        uploaded_files = request.files.getlist("file[]")
        logger.info(u"文件: %s " % str(uploaded_files))
        for file in uploaded_files:

            if file and allowed_file(file.filename):
                # filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER_DEVICE'], file.filename))
                # print file
        return redirect(url_for('device'))
    return u"""
    <!doctype html>
    <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

    <h1>FSU列表上传</h1>
    <form action="" method=post enctype="multipart/form-data">
      <p><input type="file" name="file[]" multiple="">
         <input type=submit value=上传>
    </form>
    <p>%s</p>
    """ % ("<br>".join(os.listdir(app.config['UPLOAD_FOLDER_DEVICE'], ))).encode("utf-8").decode("utf-8")


@app.route("/action", methods=['GET', 'POST'])
def action():
    if request.method == 'POST':
        logger.info(u">>开始更新update_fsu_dict")
        try:
            fsu_list_file_name = request.values.get("filename", "")  # 获取上传的文件名
            fsu_list_file = "".join([UPLOAD_FOLDER_LIST, fsu_list_file_name])  # 拼接列表
            # print fsu_list_file
            # timestr = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M") #日期
            fsu_new_name = "fsu_config_%s.pkl" % ("bak")  # 备份fsu_config
            fsu_new_path = "".join([FSU_DICT_PATH, fsu_new_name])  # 备份fsu_config 的路径
            try:
                shutil.copyfile(FSU_DICT_FILE, fsu_new_path)  # cp备份
            except:
                pass
            fsu_update_list = load_fsu_list(fsu_list_file)
            # print u"更新fsu_dict长度",len(fsu_update_list)
            logger.info(u"更新fsu_dict长度: %s " % len(fsu_update_list))

            if request.values.get("update_nkt", False):
                fsu_update_list_device = load_fsu_device(UPLOAD_FOLDER_DEVICE, fsu_update_list, NOT_KT=True)
                kt_flag = u"[屏蔽空调]"
            else:
                fsu_update_list_device = load_fsu_device(UPLOAD_FOLDER_DEVICE, fsu_update_list)
                kt_flag = u""

            # print u"已更新fsu_dict",len(fsu_update_list_device)
            logger.info(u"fsu_device_len: %s " % len(fsu_update_list_device))
            logger.info(u"fsu_device: %s " % str(fsu_update_list_device))
            logger.info(u"fsu_list: %s " % str(fsu_update_list))
            diff_fsu_set = set(fsu_update_list) - set(fsu_update_list_device)
            # print "diff",len(diff_fsu_set)
            logger.info(u"缺少关联设备的FSU: %s " % str(diff_fsu_set))
            if len(diff_fsu_set):
                shutil.copyfile(fsu_new_path, FSU_DICT_FILE)
                alert_text = u"%s更新失败,配置已回滚!,设备列表不匹配,缺少:%s" % (kt_flag, str(diff_fsu_set))
                logger.info(u"%s更新失败,配置已回滚!,设备列表不匹配,缺少:%s" % (kt_flag, str(diff_fsu_set)))
            else:
                alert_text = u"%s更新成功,更新条目:%s" % (kt_flag, len(fsu_update_list))
                logger.info(u"%s更新成功,更新条目:%s" % (kt_flag, len(fsu_update_list)))

            return u"""
                    <!doctype html>
                    <title>FSU列表上传</title>

                    <h1>FSU配置更新管理</h1>
                     <button onclick="location.href='/list'">FSU列表上传</button>
                    <button onclick="location.href='/device'">FSU关联设上传</button>
                    <button  onclick="location.href='/action'">更新配置</button>
                    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
					<button  onclick="location.href='/cha_val'">修改站点数据</button>
                    <hr>

                    <h1>更新配置表</h1>
                <form action = "" method = "post">
                    <input type="text" name="filename" value="输入提交的列表EXCEL文件"/>
                    <br>
                    <input type="submit" name="update" value="更新配置表" />
                    <input type="submit" name="update_nkt" value="更新配置表-剔除空调设备" />
                    </form>
                    <script>
                    alert("%s");
                    </script>

                    """ % (alert_text)

        except Exception as e:
            try:
                shutil.copyfile(fsu_new_path, FSU_DICT_FILE)
            except:
                pass
            logger.info(u"更新失败,回滚配置,原因:%s" % (e))
            return u"""
            <!doctype html>
            <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

            <h1>更新配置表</h1>
        <form action = "" method = "post">
            <input type="text" name="filename" value="update_fsu_list.xls"/>
            <br>
            <input type="submit" name="update" value="更新配置表" />
            <input type="submit" name="update_nkt" value="更新配置表-剔除空调设备" />
            </form>
            <script>
            alert("更新失败,配置已回滚! %s");
            </script>

            """ % e

    return u"""
            <!doctype html>
            <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

            <h1>更新配置表</h1>
        <form action = "" method = "post">
            <input type="text" name="filename" value="update_fsu_list.xls"/>
            <br>
            <input type="submit" name="update" value="更新配置表" />
            <input type="submit" name="update_nkt" value="更新配置表-剔除空调设备" />
            </form>
            """


@app.route("/add_fsu", methods=['GET', 'POST'])
def add_fsu():
    message = request.values.get("message", "")

    if request.method == 'POST':
        # logger.info(u">>查询,upload_device")
        fsu_id = request.values.get("fsuid", False)
        if not fsu_id:
            return redirect(url_for('add_fsu', message=u"FSU ID 不能为空"))

        query_bt = request.values.get("query", False)
        run_bt = request.values.get("run", False)

        if query_bt:
            logger.info(u">>设备查询,FSU:%s")
            FSU_DICT = load_fsu_config()
            fsu_config = FSU_DICT.get(fsu_id, False)
            if not fsu_config:
                return redirect(url_for('add_fsu', message=u"服务器上没有此FSU配置,请确认是否在本机添加！"))

            return redirect(
                url_for('add_fsu', message=u"FSU_id:%s 关联设备为:\n %s" % (fsu_id, str(fsu_config["device_list"]))))

        if run_bt:
            logger.info(u">>设备执行,FSU:%s")
            subprocess.call(
                '''docker run -d -h %s --privileged -v /home/fsu_env/:/home/ -v   /etc/xl2tpd/xl2tpd.conf:/etc/xl2tpd/xl2tpd.conf   -v /etc/ppp/peers/ttvpn.l2tpd:/etc/ppp/peers/ttvpn.l2tpd --restart always   --name %s  -m 100m fsu:v9  /bin/sh -c "/home/watch_dog"'''
                % (fsu_id, fsu_id), shell=True)
            subprocess.call('docker cp  json/device_resp.json %s:/usr/local/device_resp.json'%(fsu_id), shell=True)
            return redirect(url_for('add_fsu', message=u"已尝试运行FSU:%s,请登录DOCKER管理平台查看" % (fsu_id)))

            # return redirect(url_for('add_fsu'))
    return u"""
    <!doctype html>
    <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

    <h1>FSU列表上传</h1>
    <form action="" method=post enctype="multipart/form-data">
      <p><input type="text" name="fsuid" value=""/>
         <input type=submit name="query" value=查询设备>
         <input type=submit name="run" value=运行FSU>
    </form>
    <p style="color:red">%s</p>
    """ % (message)
	
@app.route("/cha_val", methods=['GET', 'POST'])
def cha_val():
    if request.method == 'POST':
        fsu_id = request.values.get("fsuid", False)
        if not fsu_id:
            return redirect(url_for('cha_val', message=u"FSU ID 不能为空"))
        dowload = request.values.get("dowload", False)
        if dowload:
            subprocess.call('docker cp %s:/usr/local/device_resp.json json/device_resp_base_%s.json'%(fsu_id,fsu_id), shell=True)
        signal = request.values.get("signal", False)
        if not signal:
            return redirect(url_for('cha_val', message=u"signalID 不能为空"))
        val = request.values.get("val", False)
        if not val:
            return redirect(url_for('cha_val', message=u"val 不能为空"))
        change = request.values.get("change", False)
        if change:
            chang_device_resp(fsu_id,signal,val)
            return redirect(url_for('cha_val', message=u"%s站点已修改测点%s的上送值为%s"%(fsu_id,signal,val)))
        upload = request.values.get("upload", False)
        if upload:
            subprocess.call('docker cp  json/device_resp_base_%s.json %s:/usr/local/device_resp.json'%(fsu_id,fsu_id), shell=True)
            return redirect(url_for('cha_val', message=u"已修改FSU:%s,请登录平台查看" % (fsu_id)))
    return u"""<!doctype html>
    <title>FSU列表上传</title>

    <h1>FSU配置更新管理</h1>
     <button onclick="location.href='/list'">FSU列表上传</button>
    <button onclick="location.href='/device'">FSU关联设上传</button>
    <button  onclick="location.href='/action'">更新配置</button>
    <button  onclick="location.href='/add_fsu'">FSU查询/运行</button>
	<button  onclick="location.href='/cha_val'">修改站点数据</button>
    <hr>

    <h1>修改站点数据</h1>
    <form action="" method=post enctype="multipart/form-data">
      <p><input type="text" name="fsuid" value="FusId"/>
      <input type=submit name="dowload" value=下载配置文件></p>
        </p> <input type="text" name="signal" value="填写信号量"/>
	<input type="text" name="val" value="填写信号值"/>
         <input type=submit name="change" value=修改></p>
    <p><input type=submit name="upload" value=上传配置文件></p>
    </form>""" 


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8088, debug=True)
