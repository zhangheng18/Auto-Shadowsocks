import re
import os
import json
import time
import base64
import requests
import binascii
import pyzbar.pyzbar as zbar
from io import BytesIO
from PIL import Image
from Cryptodome.Cipher import AES
from Cryptodome.Util import Counter


def Get_Endata():
    """从URL中获取纯文本信息"""
    
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; rv:59.0) Gecko/20100101 Firefox/59.0'}
    url= "http://free-ss.tk/" 
    s = requests.session()
    try:
        print("正在获取信息。。。。。。")
        html = s.get(url,headers=headers,timeout=5).text
        
        a,b = re.findall(r"\'(.*?)\'",html)[9:11]
        img_c  = re.findall(r"data:image/png;base64,(.*)'",html)[0]
        img_c = BytesIO(base64.b64decode(img_c))
        img = Image.open(img_c)
        c = zbar.decode(img)[0].data.decode()
        
        p_data = {'a':a,'b':b,'c':c}
        enmsg = s.post(url+"data.php",headers=headers,data=p_data,timeout=3)
        endata = base64.b64decode(enmsg.text)
        
        key = bytes(a,encoding="utf-8")
        iv = bytes(b,encoding="utf-8")
        mode  = re.findall(r"CryptoJS.mode.(\w{3})",html)
        print("获取信息成功。。。。。。。")
        return endata,key,iv,mode
    except:
        print("获取失败。。。。。。")


def Dec_data(mode,key,iv,endata):
    try:
        #print(mode,key,iv)
        # 初始化AES解密方式
        if mode == [] or mode[0] == 'CBC':
            aes = AES.new(key,AES.MODE_CBC,iv)
        elif mode[0] == 'ECB':
            aes = AES.new(key,AES.MODE_ECB)
        elif mode[0] == 'CFB':
            aes = AES.new(key,AES.MODE_CFB,iv,segment_size=128)
        elif mode[0] == 'OFB':
            aes = AES.new(key,AES.MODE_OFB,iv)
        elif mode[0] == 'CTR':
            ctr = Counter.new(128, initial_value=int(binascii.hexlify(iv), 16))
            aes = AES.new(key,AES.MODE_CTR,counter=ctr)
        else:
            print('获取加密方式错误。。。。')

        ss = re.findall(r'{.*}',aes.decrypt(endata).decode('utf-8'))[0]
        ss_data = json.loads(ss)['data']
        print("解密成功")
        return ss_data
    except:
        print("解密失败！")


def Read_Config(filename="gui-config.json"):
    try:
        with open(filename,'r',encoding='utf-8') as f_obj:
            guiconfig = json.load(f_obj)
        print("读取配置文件成功。。。")
        return guiconfig
    except FileNotFoundError:
        msg = "文件 " + filename + " 并不存在，请确认程序运行在Shadowsocks目录中！"
        print(msg)
    


def Write_Config(guiconfig,ss_data,filename="gui-config.json"):
    configs = []

    counts = 0
   
    for ss in ss_data:
        config = {}

        #移除低分
        try:
            if sum(map(int,ss[0].split('/'))) < 34:
                continue
        except:
            pass

        #限制获取数量为10
        counts += 1
        if(counts > 10):
            break

        if (re.match(r"aes|rc4|chacha",ss[3])):
            ss[3],ss[4] = ss[4],ss[3] 
        
        config["password"] = ss[3]
        config["method"] =  ss[4]

        config["server"] = ss[1]
        config["server_port"] = ss[2]
        
        config["plugin"] =  ""
        config["plugin_opts"] =  ""
        config["remarks"] = "{}[{}]({})".format(ss[6],ss[0],ss[5])
        config["timeout"] = 2
        configs.append(config)
    guiconfig['configs'] = configs

    print('正在写入文件……')
    print('此次更新了'+str(len(configs))+'条数据')
    try:
        with open(filename,'w',encoding='utf-8') as f_obj:
            f_obj.write(json.dumps(guiconfig,ensure_ascii=False,indent=2))
        print('写入文件完成！')
    except FileNotFoundError:
        msg = "文件 " + filename + " 并不存在，请确认程序运行在Shadowsocks目录中！"
        print(msg)


def Kill_SS():
        try:
            os.system("taskkill /F /IM Shadowsocks.exe /T")
        except:
            pass

def Start_SS():
    os.startfile("Shadowsocks.exe")


if __name__ == '__main__':

    endata,key,iv,mode = Get_Endata()
    ss_data = Dec_data(mode,key,iv,endata)
    guiconfig = Read_Config()
    
    Kill_SS()
    Write_Config(guiconfig,ss_data)
    Start_SS()

    print("3s后关闭......")
    time.sleep(3)
