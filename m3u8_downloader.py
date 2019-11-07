#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 数字长度模块
import math
# 复制模块
import copy
# 系统操作模块
import os,sys,time
# 正则模块
import re
# 删除目录模块
import shutil
# 多线程模块
from concurrent.futures import *
# 下载模块
import requests
#进度条模块
from progressbar import *
#AES 加密解密
from Crypto.Cipher import AES
from urllib.parse import urlparse

##############
###全局变量###
##############

# 反爬浏览器头
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
}

# 存储完整下载地址
dow_list = []

# 存储下载失败的文件
fail_list = []

# 存储ts加密key
key = ""

# 禁止 request 告警(忽略ssl验证时会产生告警)
requests.packages.urllib3.disable_warnings()

##############
####主程序####
##############

# 下载ts片段文件
def dowload_data(data_url):
    name = data_url[-9:]
    if not os.path.exists('./bak/' + name):
        # 下载文件
        data = requests.get(url=data_url, headers=headers, timeout=300, verify=False)
        if data.status_code == 200:
            # 写入片段文件
            with open('./bak/' + name, 'wb') as code:
                code.write(data.content)
        else:
            print('fail: %s' %data_url)
            fail_list.append(data_url)
    return 0


# 合并ts片段文件
def merge_movie(name, movie_name):
    if name in fail_list:
        return 0
    filename = name[-9:]
    if os.path.exists('./bak/' + filename):
        # 读出片段
        with open('./bak/' + filename, 'rb') as code:
            if len(key): # AES 解密
                cryptor = AES.new(key, AES.MODE_CBC, key)  
                data = cryptor.decrypt(code.read())
            else:
                data = code.read()
        # 拼接到新文件
        with open(movie_name+'.ts', 'ab') as code:
            code.write(data)
            # 清空变量
            data = None
    else:
        fail_list.append(name)

# 主程序
def dow_m3u8(target, movie_name, pool_num):
    global key

    dow_cur = 0 #当前下载个数
    mer_cur = 0 #当前合并个数
    base_url = ''

    #进度条切割
    widgets = ['下载进度：', Percentage(), ' ', Bar(marker=RotatingMarker('>-=')),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=10000).start()

    # 下载分析文件
    file_req = requests.get(url=target, headers=headers, timeout=30, verify=False)
   
    if "#EXTM3U" not in file_req.text:
        raise BaseException("非M3U8的链接")
 
    base_url = target.rsplit("/", 1)[0] + "/" 
    base_url_sec = ""

    if "EXT-X-STREAM-INF" in file_req.text:  # 第一层 (此标志表示存在两层 m3u8)
        file_line = file_req.text.split("\n")
        for line in file_line:
            if '.m3u8' in line:  #两层 m3u8
                if line[0:1] == "/":  #以斜杠开头，直接提取域名
                    res  = urlparse(target)
                    base_url = res.scheme + "://" + res.netloc
                else:
                    if "/" in line:  #不以斜杠开头，但是中间带了路径
                        base_url_sec = target.rsplit("/", 1)[0] + "/" + line.rsplit("/",1)[0] + "/"

                url = base_url + line # 拼出第二层m3u8的URL
                print('second: %s' %url)
                file_req = requests.get(url=url, headers=headers, timeout=30, verify=False)

        if base_url_sec: 
            base_url = base_url_sec #提取完第二层m3u8，之后的url都以二层base_url_sec 为参照
        
 
    file_line = file_req.text.split("\n")
 

    for index, line in enumerate(file_line): # 第二层
        if "#EXT-X-KEY" in line:  # 找解密Key
            method_pos = line.find("METHOD")
            comma_pos = line.find(",")
            method = line[method_pos:comma_pos].split('=')[1]
            print("Decode Method：%s" %method)
            
            uri_pos = line.find("URI")
            quotation_mark_pos = line.rfind('"')
            key_path = line[uri_pos:quotation_mark_pos].split('"')[1]
            
            key_url = base_url + key_path # 拼出key解密密钥URL
            res = requests.get(url=key_url, headers=headers, timeout=30, verify=False)
            key = res.content
            print("key：%s " %key)

    # 分析文件
    file_name_list = re.findall('(\n[^#]*?).ts', file_req.text)

    # 判断目录是否存在
    os.makedirs('bak') if os.path.exists('bak') == False else None
    # 删除已存在的合并文件
    os.remove(movie_name + '.ts') if os.path.exists(movie_name + '.ts') == True else None
   
    for i in file_name_list:
        # 筛选有用的行
        file_name = str(i).replace('\n', '')
        # 拼接下载路径
        if file_name[0:1] == "/":
            res  = urlparse(target)
            base_url = res.scheme + "://" + res.netloc
        dowload_url = base_url + file_name + '.ts'
        # 把路径传递到列表里面
        dow_list.append(dowload_url)

    # 创建线程池指定最大线程数
    with ThreadPoolExecutor(max_workers=int(pool_num)) as t:
        obj_list = []
        for each in dow_list:
            obj = t.submit(dowload_data, each)
            obj_list.append(obj)
         
        for result in as_completed(obj_list):
            dow_cur += 1
            # 计算进度值，取整数
            per = math.floor(dow_cur * 10000 / int(len(dow_list)))
            pbar.update(per) #更新进度条
    pbar.finish() #关闭进度条
            
    # 重新下载 fail 文件
    if fail_list:
        fail_reload_list = copy.deepcopy(fail_list)
        fail_list.clear()
        print("redowloading fail file list ......")
        with ThreadPoolExecutor(max_workers=int(pool_num)) as t:
            obj_list.clear()
            for each in fail_reload_list:
                obj = t.submit(dowload_data, each)
                obj_list.append(obj)
            for result in as_completed(obj_list):
                pass
            print("fail file download finished ......")

    #进度条切割
    widgets = ['合并进度：', Percentage(), ' ', Bar(marker=RotatingMarker('>-=')),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=10000).start()

    # 下载片段完成 顺序合并片段文件
    for i in dow_list:
        merge_movie(i, movie_name)
        # 计算进度值，取整数
        mer_cur += 1
        per = math.floor(mer_cur * 10000 / int(len(dow_list)))
        pbar.update(per) #更新进度条

    pbar.finish() #关闭进度条
    # 删除片段文件目录
    # shutil.rmtree('bak')

# 程序入口
if __name__ == '__main__':
    # 获取文本框数据
    if len(sys.argv) != 3:
        print("\nUsage: python3 %s url  filename" %sys.argv[0])
        exit(1)
    target = sys.argv[1]
    movie_name = sys.argv[2]
    pool_num = 32
    # 执行主程序
    print('\n\n')
    dow_m3u8(target, movie_name, pool_num)
    print("---------- fail list ----------")
    for each in fail_list:
        print(each)
    print("---------- finished -----------")
