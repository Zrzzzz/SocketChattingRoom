import pyaudio
import wave
import time
import os
import sys

def recordwav(t, fileurl, isrecoding=None):
    CHUNK = 1024  # 缓存大小
    FORMAT = pyaudio.paInt16  # 比特
    CHANNELS = 1  # 声道
    RATE = 32000  # 采样率
    RECORD_SECONDS = t  # 录制时间
    WAVE_OUTPUT_FILENAME = fileurl  # 输出地址
    # close 错误输出
    # os.close(sys.stderr.fileno())
    
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=False,
                        frames_per_buffer=CHUNK)

        frames = []

        if t == 0:
            while isrecoding:
                data = stream.read(CHUNK)
                frames.append(data)
        else:
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)    

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
    except Exception as err:
        print(err)
    # os.open(sys.stderr.fileno())
    return os.path.abspath(fileurl)


def playwav(fileurl):
    wf = wave.open(fileurl, 'rb')
    p = pyaudio.PyAudio()

    # 回调方式播放
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


if __name__ == '__main__':
    recordwav(3, 'out.wav')
    # playwav('UserData/Cache/1617630820.wav')
