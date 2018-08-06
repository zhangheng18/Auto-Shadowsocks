import re
import os
import json
import time

import base64
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode

import requests

import binascii
from Cryptodome.Cipher import AES
from Cryptodome.Util import Counter

import logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s :%(levelname)s : %(message)s')

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; rv:62.0) Gecko/20100101 Firefox/62.0'
}


class Freess(object):
    def __init__(self):
        self.data = {}

    def get_Data(self):
        """获取加密信息"""
        try:
            url = "http://free-ss.tk/"
            p_data = {}

            logging.info("正在读取 {}".format(url))
            keep_http = requests.session()
            html = keep_http.get(url, headers=headers, timeout=3).text

            #移除注释内容
            html = re.sub(r"/\*{1,2}[\s\S]*?\*/", "", html)

            p_data['a'] = re.findall(r"var a='(.*?)'", html)[1]
            p_data['b'] = re.findall(r"var b='(.*?)'", html)[1]
            p_data['c'] = re.findall(r"var c='(.*?)'", html)[1]

            #从image提取数据
            img_base64 = re.findall(r"data:image/png;base64,(.*)'", html)[0]
            img = BytesIO(base64.b64decode(img_base64))
            img_data = decode(Image.open(img))[0].data.decode()
            p = re.findall(r'function\((.)\){\n', html)[0]
            p_data[p] = img_data
            entext = keep_http.post(
                url + "data.php", headers=headers, data=p_data, timeout=2)
            endata = base64.b64decode(entext.content)

            # import ipdb
            # ipdb.set_trace()
            key = bytes(p_data['a'], encoding="utf-8")
            iv = bytes(p_data['b'], encoding="utf-8")

            self.decrypt_data(key, iv, endata)
        except Exception as e:
            logging.error("网络异常 ...正在重试")

    def decrypt_data(self, key, iv, endata):
        """解密数据得到ss信息"""
        ctr = Counter.new(128, initial_value=int(binascii.hexlify(iv), 16))
        modes = [
            AES.new(key, AES.MODE_ECB),
            AES.new(key, AES.MODE_CBC, iv),
            AES.new(key, AES.MODE_OFB, iv),
            AES.new(key, AES.MODE_CTR, counter=ctr),
            AES.new(key, AES.MODE_CFB, iv, segment_size=128),
        ]

        for mode in modes:
            try:
                dec = mode.decrypt(endata).decode('utf-8')
                ss = re.findall(r'{.*}', dec)
                self.data = json.loads(ss[0])['data']
                break
            except:
                pass
    


def Read_Config(filename="gui-config.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f_obj:
            guiconfig = json.load(f_obj)
        logging.info("读取{}。。。".format(filename))
        return guiconfig
    except FileNotFoundError:
        msg = filename + " 并不存在，请确认程序运行在Shadowsocks目录中！"
        logging.error(msg)


def Write_Config(guiconfig, ss_data, filename="gui-config.json"):
    configs = []

    #检测是否password列和method位置不对
    swap_flag = True if re.search(r'cfb|gcm|cha|md', ss_data[0][3]) else False
    for ss in ss_data[:6]:
        config = {}

        if swap_flag:
            ss[3], ss[4] = ss[4], ss[3]

        config["password"] = ss[3]
        config["method"] = ss[4]
        config["server"] = ss[1]
        config["server_port"] = ss[2]
        config["plugin"] = ""
        config["plugin_opts"] = ""
        config["remarks"] = "{}[{}]({})".format(ss[6], ss[0], ss[5])
        config["timeout"] = 2
        configs.append(config)
    guiconfig['configs'] = configs

    logging.info('正在写入文件……')
    logging.info('此次更新了' + str(len(configs)) + '条数据')
    try:
        with open(filename, 'w', encoding='utf-8') as f_obj:
            f_obj.write(json.dumps(guiconfig, ensure_ascii=False, indent=2))
        logging.info('写入文件完成！')
    except FileNotFoundError:
        msg = "文件 " + filename + " 并不存在，请确认程序运行在Shadowsocks目录中！"
        logging.error(msg)


def Kill_SS():
    """杀死shadowsocks"""
    logging.info("重启 Shadowsocks")
    os.system("taskkill /F /IM Shadowsocks.exe /T")


def Start_SS():
    """启动 shadowsocks"""
    os.startfile("Shadowsocks.exe")


if __name__ == '__main__':
    ss = Freess()

    #有时会因为网络原因请求失败，尝试3次
    for i in range(3):
        ss.get_Data()
        if not ss.data:
            logging.info("获取内容失败，重试ing")
            continue
        guiconfig = Read_Config()
        Kill_SS()
        Write_Config(guiconfig, ss.data)
        Start_SS()

        logging.info("3s后关闭......")
        time.sleep(3)
