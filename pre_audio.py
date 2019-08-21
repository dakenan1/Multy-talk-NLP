#!/usr/bin python
# -*- coding: utf-8 -*-
# @File    : pre_audio.py
"""
用于声音模块的处理
1、录制音频：录制音频能够自动控制录制的时长
2、播放音频
"""
# TODO 自动适应录音
import pyaudio
import wave
import time
from sys import byteorder
from array import array
from struct import pack
from playsound import playsound
THRESHOLD = 500
CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 16000


def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD


def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384  # 2的14次方
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def trim(snd_data):
    "Trim the blank spots at the start and end"

    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data


def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in range(int(seconds * RATE))])
    r.extend(snd_data)
    r.extend([0 for i in range(int(seconds * RATE))])
    return r


def record_sub():
    """
        Record a word or words from the microphone and
        return the data as an array of signed shorts.

        Normalizes the audio, trims silence from the
        start and end, and pads with 0.5 seconds of
        blank sound to make sure VLC et al can play
        it without getting chopped off.
        """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK)

    num_silent = 0
    snd_started = False
    r = array('h')

    while True:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r


def record(audio_file):
    """
    录音文件夹地址
    :param audio_file:
    :return: True/False
    """
    sample_width, data = record_sub()
    data = pack('<' + ('h' * len(data)), *data)

    try:
        wf = wave.open(audio_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)  
        wf.writeframes(data)
        wf.close()
        return True
    except BaseException as e:
        print(e)
        return False


def play_wave(audio_file):
    try:
        wf = wave.open(audio_file, 'rb')

        p = pyaudio.PyAudio()

        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=callback)

        stream.start_stream()

        while stream.is_active():
            time.sleep(0.1)

        stream.stop_stream()
        stream.close()
        wf.close()

        p.terminate()
        return True

    except BaseException as e:
        print(e)
        return False


def play(audio_file):
    try:
        playsound(audio_file)
        return True
    except BaseException as e:
        return False

if __name__ == '__main__':
    print('收集录音')
    record('./output.wav')
    print("录音完毕")
    is_play = play_wave('./output.wav')

    if is_play:
        print("播放完毕")
    else:
        print("播放失败")
