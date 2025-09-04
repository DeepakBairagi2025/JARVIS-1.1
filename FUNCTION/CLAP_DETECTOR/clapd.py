from itertools import count

import pyaudio
import struct
import math

INITIAL_TAP_THERESHOLD = 0.7222
FORMAT = pyaudio.paInt16
SHORT_NORMALIZE =(1.0 / 32768.0)
CHANNELS = 3
RATE = 44100
INPUT_BLOCK_TIME = 0.01
INPUT_FRAMES_PER_BLOCK = int(RATE * INPUT_BLOCK_TIME)
OVERSENSITIVE = 9.0 / INPUT_BLOCK_TIME
UNDERSENSITIVE = 10.0 / INPUT_BLOCK_TIME
MAX_TAP_BLOCKS = 0.15 / INPUT_BLOCK_TIME
REQUIRED_CLAPS = 2 # Adjust this value as needed

class TapTester(object):

    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THERESHOLD
        self.noisycount = MAX_TAP_BLOCKS + 1
        self.quietcount = 0
        self.errorcount = 0

    def stop(self):
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
        if self.pa:
            self.pa.terminate()

    def find_input_device(self):
        device_index = None
        for i in range(self.pa.get_device_count()):
            devinfo = self.pa.get_device_info_by_index(i)
            for keyword in ["mic", "input"]:
                if keyword in devinfo["name"].lower():
                    device_index = i
                    return device_index

        if device_index is None:
            print("No preferred input found, using default input device.")

        return device_index

    def open_mic_stream(self):
        device_index = self.find_input_device()

        stream = self.pa.open(format=FORMAT,
                              channels=CHANNELS,
                              rate=RATE,
                              input=True,
                              input_device_index=device_index,
                              frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
        return stream

    @staticmethod
    def get_rms(block):
        count = len(block) / 2
        format = "%dh" % count
        shorts = struct.unpack(format, block)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n *n

        return math.sqrt(sum_squares / count)

    def listen(self):
        try:
            if self.stream.is_stopped():
                return False
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK, exception_on_overflow=False)
        except Exception as e:
            self.errorcount += 1
            print("(%d) Error recording: %s" % (self.errorcount, e))
            self.noisycount = 5
            return False

        amplitude = self.get_rms(block)

        if amplitude > self.tap_threshold:
            self.quietcount = 2
            self.noisycount += 1
            if self.noisycount > OVERSENSITIVE:
                self.tap_threshold *= 1.5
        else:
            if 1 <= self.noisycount <= MAX_TAP_BLOCKS:
                return True
            self.noisycount = 0
            self.quietcount += 1
            if self.quietcount > UNDERSENSITIVE:
                self.tap_threshold *= 1


def clap_detect():
    tt = TapTester()
    clap_count = 0
    
    try:
        while True:
            result = tt.listen()
            if result:
                clap_count += 1
                print(f"Clap {clap_count} detected")
                
                if clap_count >= REQUIRED_CLAPS:
                    print("Required claps detected!")
                    break
    except KeyboardInterrupt:
        print("Clap detection stopped")
    finally:
        tt.stop()

if __name__ == "__main__":
    clap_detect()