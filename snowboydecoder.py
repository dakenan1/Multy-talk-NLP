#!/usr/bin/env python
#-*- coding: utf-8 -*-
import collections
import pyaudio
import subprocess
import snowboydetect
import time
import wave
import os
import WebaiuiDemo
import logging
import requests
import sys
from AR_realtime.src.run import myThread
#import AR-realtime.src.run

reload(sys)
sys.setdefaultencoding('utf8')

logging.basicConfig()
logger = logging.getLogger("snowboy")
logger.setLevel(logging.INFO)
TOP_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")
DETECT_DONG = os.path.join(TOP_DIR, "resources/dong.wav")
DETECT_LUCY = os.path.join(TOP_DIR, "resources/chaowei_lucy.wav")

TIME = 2
TIME1 = 3
class RingBuffer(object):
    """Ring buffer to hold audio from PortAudio"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        self._buf.extend(data)

    def get(self):
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


def play_audio_file(fname=DETECT_DING):
    ding_wav = wave.open(fname, 'rb')
    #print(ding_wav.getsampwidth())  # 2
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    audio = pyaudio.PyAudio()

    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(), input=False, output=True)
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()


class HotwordDetector(object):
    def __init__(self, decoder_model,
                 resource=RESOURCE_FILE,
                 sensitivity=[],
                 audio_gain=1):

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode())
        self.detector.SetAudioGain(audio_gain)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())

        self.ring_buffer = RingBuffer(self.detector.NumChannels() * self.detector.SampleRate() * 5)
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(
            input=True,
            output=False,
            format=self.audio.get_format_from_width(self.detector.BitsPerSample() / 8),
            channels=self.detector.NumChannels(),
            rate=self.detector.SampleRate(),  # Sampling rate =16000
            frames_per_buffer=2048,
            stream_callback=audio_callback)


    def start(self, detected_callback=play_audio_file,
              interrupt_check=lambda: False,
              sleep_time=0.03):
        w_start1 = 'text":"'
        w_start2 = '"question":"'
        w_end1 = '","type'  
        w_end2 = '","question_ws"' 
        if interrupt_check():
            logger.debug("detect voice return")
            return

        tc = type(detected_callback)
        if tc is not list:
            detected_callback = [detected_callback]
        if len(detected_callback) == 1 and self.num_hotwords > 1:
            detected_callback *= self.num_hotwords

        assert self.num_hotwords == len(detected_callback), \
            "Error: hotwords in your models (%d) do not match the number of " \
            "callbacks (%d)" % (self.num_hotwords, len(detected_callback))

        logger.debug("detecting...")

        while True:
            if interrupt_check():
                logger.debug("detect voice break")
                break
            data = self.ring_buffer.get()

            #print(len(data))
            if len(data) == 0:
                time.sleep(sleep_time)
                continue

            #print("data2:", len(data))
            ans = self.detector.RunDetection(data)
            if ans == -1:
                logger.warning("Error initializing streams or reading audio data")
            elif ans > 0:
                message = "Keyword " + str(ans) + " detected at time: "
                message += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                logger.info(message)
                callback = detected_callback[ans-1]
                if callback is not None:
                    callback()
                #break  ###############
                logger.debug("finished.")

                # 唤醒后lucy

                #time.sleep(3)    
                #subprocess.call("python2 WebaiuiDemo.py", shell=True)
                print('start to run')
                contents = WebaiuiDemo.run(TIME)
                ans = WebaiuiDemo.extract(contents,w_start1,w_end1)
                result = ans[:ans.find("\"")]
                ques = WebaiuiDemo.extract(contents, w_start2, w_end2)
                
                #requests.post("http://192.168.1.108/speak/speak2.act",data={'text': result})  #send http Request

                print("answer==%s"%(result))
                print("question==%s"%(ques))
                #subprocess.call("python run.py", shell=True)

                #图像检测线程打开
                # 创建新线程
                thread1 = myThread(1, "Thread-1", 1)
                # 开启新线程
                thread1.start()

                while len(ans):    
                    contents = WebaiuiDemo.run(TIME1)
                    ans = WebaiuiDemo.extract(contents,w_start1,w_end1)
                    result = ans[:ans.find("\"")]
                    ques = WebaiuiDemo.extract(contents,w_start2,w_end2)
                    print("answer==%s"%(result))
                    print("question==%s"%(ques))
                    if ques == "你可以模仿我的表情吗":
                        thread1.setFlag(1)
                    '''
                    elif ques == "你可以模仿我的动作吗":
                        thread1.setFlag(1)

                    elif ques == "你可以模仿我的声音吗":
                    '''   
                    #requests.post("http://192.168.1.108/speak/speak2.act",data={'text': result})  #send http Request

    def terminate(self):
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()


