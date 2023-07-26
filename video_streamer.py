#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess

from mavlink_connection import *
from gst_stream import *





class video_streamer(object):
    CONFIG_FILE = "/boot/rclink4g.conf"
    SNAPSHOT_DIR = "snapshots"
    STREAM_DEFS = [
        [None,None],
        ["160x120",2],
        ["640x480",2],
        ["640x480",None],
        ["1920x1080",0],
    ]



    def __init__(self):
        self._finished = False
        os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)
        self._read_config()
        #self.mav_conn = mavlink_connection(self, "udp:0.0.0.0:14550")
        self.mav_conn = mavlink_connection(self, "udp:localhost:14551")

        # === usb camera ===
        video_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 ! videorate ! video/x-raw,width=640,height=480,framerate=15/1 ! videoconvert"
        stream_cmd = "v4l2h264enc extra-controls=controls,video_bitrate=1000000,h264_i_frame_period=15 ! 'video/x-h264,level=(string)3' ! rtph264pay ! udpsink clients="
        record_cmd = "v4l2h264enc extra-controls=controls,video_bitrate=1000000,h264_i_frame_period=15 ! 'video/x-h264,level=(string)3' ! avimux ! filesink location="
        snapshot_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! image/jpeg,width=,height= ! filesink location="
        # === pi camera ===
        #video_cmd = f"gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-h264,width=640,height=480,framerate=15/1 ! h264parse"
        #stream_cmd = "rtph264pay ! udpsink clients="
        #record_cmd = "avimux ! filesink location="
        #snapshot_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! image/jpeg,width=,height= ! filesink location="
        self.stream = gst_stream("rclink4g_stream", video_cmd, stream_cmd, record_cmd, snapshot_cmd)
        self.stream.start()

        # setup the sighup handler
        signal.signal(signal.SIGHUP, self.handle_sighup)



    def close(self):
        self._finished = True
        self.mav_conn.close()



    def _read_config(self):
        print("reading config file..")
        self.ground_station_address = self._get_config_value("ground_station_address")
        self.ground_station_video_port = int(self._get_config_value("ground_station_video_port"))
        self.video_channel = int(self._get_config_value("video_channel"))
        self.video_stream_settings = [None]
        self.video_stream_settings.append(int(self._get_config_value("video_stream_1")))
        self.video_stream_settings.append(int(self._get_config_value("video_stream_2")))
        self.video_stream_settings.append(int(self._get_config_value("video_stream_3")))
        self.video_stream_settings.append(int(self._get_config_value("video_stream_4")))

        print(f"ground_station_address={self.ground_station_address}")
        print(f"ground_station_video_port={self.ground_station_video_port}")
        print(f"video_channel={self.video_channel}")
        print(f"video_stream_settings={self.video_stream_settings}")



    def _get_config_value(self, name, default=None):
        response = default

        try:
            with open(self.CONFIG_FILE) as f:
                for line in f.readlines():
                    try:
                        param_name,param_value = [x.strip() for x in line.split("=")]

                        if param_name == name:
                            response = param_value
                    except Exception as e:
                        # line wasn't formatted name=value
                        pass
        except Exception as e:
            # fails over to given default value
            pass

        return response



    def handle_sighup(self, signal, frame):
        self._read_config()
        self.mav_conn.read_config()



    def set_video_stream(self, index):
        print(f"setting video stream to {index}..")

        stream_client = (self.ground_station_address,self.ground_station_video_port)
        stream_res,stream_fps = self.STREAM_DEFS[self.video_stream_settings[index]]

        # fps == 0 means that "snapshot" was selected for this slot
        if stream_fps == 0:
            print(f"taking {stream_res} snapshot..")
            TEMP_SNAPSHOT_PATH="/tmp/snapshot.jpg"
            subprocess.run(f"sudo rm -f {TEMP_SNAPSHOT_PATH}".split())
            self.stream.snapshot(stream_res, TEMP_SNAPSHOT_PATH)
            snapshot_time = time.strftime("%Y-%m-%d_%H%M%S")
            snapshot_file = f"{snapshot_time}.jpg"
            snapshot_path = os.path.join(self.SNAPSHOT_DIR, snapshot_file)
            subprocess.run(f"sudo mv {TEMP_SNAPSHOT_PATH} {snapshot_path}".split())
        # stream_res == None means that "none" was selected (no stream for this slot)
        elif stream_res is None:
            print("stopping stream..")
            self.stream.remove_all_clients()
        # otherwise some valid res/fps was selected for this slot
        else:
            if not self.stream.has_client_stream(stream_client, stream_res, stream_fps):
                print(f"changing stream to {stream_res} @ {stream_fps}fps..")
                self.stream.remove_all_clients()
                self.stream.add_client(stream_client, stream_res, stream_fps)
            else:
                print(f"already streaming {stream_res} @ {stream_fps}fps..")
                





if __name__ == "__main__":
    vs = video_streamer()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("exiting..")

    vs.close()
