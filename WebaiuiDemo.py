#-*- coding: utf-8 -*-
import sys
import requests
import time
import json
import hashlib
import base64
import os
import re
import wave
import pre_audio
from pyaudio import PyAudio,paInt16

reload(sys)
sys.setdefaultencoding('utf8')

URL = "http://openapi.xfyun.cn/v2/aiui"
APPID = ""
API_KEY = ""
AUE = "raw"
AUTH_ID = ""
DATA_TYPE = "audio"
SAMPLE_RATE = "16000"
SCENE = "main_box"
RESULT_LEVEL = "complete"
LAT = "39.938838"
LNG = "116.368624"
#个性化参数，需转义
PERS_PARAM = "{\\\"auth_id\\\":\\\"2894c985bf8b1111c6728db79d3479ae\\\"}"
FILE_PATH = "/home/aa/桌面/Multi-talk/01.wav"
"""录音"""
framerate=16000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME = 2
TIME1 = 3
def save_wave_file(filename,data):
    '''save the date to the wavfile'''
    wf=wave.open(filename,'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b"".join(data))
    wf.close()

def my_record(TIME):
    pa=PyAudio()
    stream=pa.open(format = paInt16,channels=1,
                   rate=framerate,input=True,
                   frames_per_buffer=NUM_SAMPLES)
    my_buf=[]
    count=0
    while count<TIME*15:#控制录音时间
        string_audio_data = stream.read(NUM_SAMPLES)
        my_buf.append(string_audio_data)   
        count+=1
        print('.')
        #os.system('cls')
    save_wave_file('01.wav',my_buf)
    stream.close()

"""录音"""

def luyin(TIME):
    my_record(TIME)
    #pre_audio.record('./01.wav')
    print('over')

def buildHeader():
    curTime = str(int(time.time()))
    param = "{\"result_level\":\""+RESULT_LEVEL+"\",\"auth_id\":\""+AUTH_ID+"\",\"data_type\":\""+DATA_TYPE+"\",\"sample_rate\":\""+SAMPLE_RATE+"\",\"scene\":\""+SCENE+"\",\"lat\":\""+LAT+"\",\"lng\":\""+LNG+"\"}"
    #使用个性化参数时参数格式如下：
    #param = "{\"result_level\":\""+RESULT_LEVEL+"\",\"auth_id\":\""+AUTH_ID+"\",\"data_type\":\""+DATA_TYPE+"\",\"sample_rate\":\""+SAMPLE_RATE+"\",\"scene\":\""+SCENE+"\",\"lat\":\""+LAT+"\",\"lng\":\""+LNG+"\",\"pers_param\":\""+PERS_PARAM+"\"}"
    paramBase64 = base64.b64encode(param)

    m2 = hashlib.md5()
    m2.update(API_KEY + curTime + paramBase64)
    checkSum = m2.hexdigest()

    header = {
        'X-CurTime': curTime,
        'X-Param': paramBase64,
        'X-Appid': APPID,
        'X-CheckSum': checkSum,
    }
    return header

def readFile(filePath):
    binfile = open(filePath, 'rb')
    data = binfile.read()
    return data

def run(TIME):
    #pre_audio.record(FILE_PATH)
    luyin(TIME)
    #data = readFile(FILE_PATH)
    #print('data======',data)
    r = requests.post(URL, headers=buildHeader(), data=readFile(FILE_PATH))
    print(r.content)
    return r.content

def extract(str0,w_start,w_end):
    #提取json文件中的回复
    a = "".join(str0)
    p1 = re.compile(w_start+'(.*?)'+w_end,re.S)
    list1 = re.findall(p1,a)
    str1 = "".join(list1)
    str2 = str1.encode('utf-8')
    #print("%s"%(str2))
    #result = str2[:str2.find("\"")]
    return str2
'''

json_content = r.content
a = "".join(json_content)
print("字符串:", type(json_content))
dict_content = json.loads(json_content)
print("dict:", dict_content)

'''
