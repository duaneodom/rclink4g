#!/usr/bin/env python3

import sys
import time
import threading

from pymavlink import mavutil





class mavlink_connection(object):
    def __init__(self, video_streamer, connection):
        self._video_streamer = video_streamer
        self._connection = connection
        self._finished = False
        self._mav = None
        self._mavlink_processing_thread_handle = None
        self._current_video_slot = 0

        self._mav = mavutil.mavlink_connection(self._connection)
        print("mavlink network connection established.")
        print(f"dialect: {mavutil.current_dialect}")
        print(f"protocol version: {self._mav.WIRE_PROTOCOL_VERSION}")

        if not self._mav:
            raise Exception("mavlink connection failed.")

        self._wait_for_heartbeat()

        # setup mavlink msg callback
        self._mav.mav.set_callback(self._on_mavlink_msg, self._mav)

        # start the message processor thread
        self._mavlink_processing_thread_handle = threading.Thread(target=self._mavlink_processing_thread, args=())
        self._mavlink_processing_thread_handle.start()



    def close(self):
        self._finished = True
        self._mavlink_processing_thread_handle.join()



    def read_config(self):
        self._current_video_slot = 0



    def handle_video_rc_channel(self, value):
        video_slot = 0

        if value <= 1250:
            video_slot = 1
        elif value > 1250 and value <= 1500:
            video_slot = 2
        elif value > 1500 and value <= 1750:
            video_slot = 3
        elif value > 1750 and value <= 2000:
            video_slot = 4
        else:
            print("invalid video slot value!")

        if video_slot != self._current_video_slot:
            self._current_video_slot = video_slot
            self._video_streamer.set_video_stream(video_slot)



    # =============== mavlink message callback ===============
    def _on_mavlink_msg(self, msg, master):
        self._mavlink_last_heartbeat = time.time()

        #print(f"received mavlink message: {msg.get_type()}")

        if msg.get_type() == "RC_CHANNELS":
            _rc_channels = [msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw, msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw]
            
            if self._video_streamer.video_channel in range(1, len(_rc_channels)+1):
                self.handle_video_rc_channel(_rc_channels[self._video_streamer.video_channel-1])



    # =============== mavlink processing thread ===============
    def _mavlink_processing_thread(self):
        while not self._finished:
            try:
                if self._mav.select(0.05):
                    msg = self._mav.recv_msg()

                    if msg and msg.get_type() != "BAD_DATA":
                        self._mav.post_message(msg)
            except TypeError as e:
                # this occurs when recv_msg receives bad/empty data so we ignore it
                #print(e)
                pass
            except Exception as e:
                #print("exception in mavlink_connection._mavlink_processing_thread!")
                #print(e)
                pass



    def _wait_for_heartbeat(self):
        got_heartbeat = False

        while not got_heartbeat and not self._finished:
            print("waiting for a MavLink heartbeat.. ", end="")
            
            try:
                msg = self._mav.recv_match(type="HEARTBEAT", timeout=3.0)
                got_heartbeat = True
            except KeyboardInterrupt:
                print("cancelled waiting for heartbeat.. exiting.")
                sys.exit(1)
            except:
                print("never received a mavlink heartbeat.. exiting.")
                sys.exit(1)

        print("got heartbeat.")






if __name__ == "__main__":
    def on_update(k,v):
        if k in ("pos","hdop","statustext"):
            print(f"{k} = {v}")

    #mc = mavlink_connection("/dev/ttyACM0", 115200, update_callback=on_update)
    #mc = mavlink_connection("/dev/ttyUSB0", 57600, update_callback=on_update)
    mc = mavlink_connection("udp:0.0.0.0:14550")
    #mc = mavlink_connection("tcp:localhost:5760")

    try:
        while True:
            time.sleep(2.0)
#            print(f"mode: {mc.mode}")
#            print(f"armed: {mc.armed}")
#            print(f"heading: {mc.heading}")
#            print(f"fence_enabled: {mc.fence_enabled}")
#            print(f"fence_radius: {mc.fence_radius}")
#            print(f"distance_home: {mc.distance_home}")

#            if mc.mode == "loiter":
#                mc.set_mode("guided", wait=True)
#            else:
#                mc.set_mode("loiter", wait=True)

#            if mc.fence_enabled:
#                mc.set("fence_enabled", False)
#            else:
#                mc.set("fence_enabled", True)

#            if mc.fence_radius == 20:
#                mc.set("fence_radius", 100)
#            else:
#                mc.set("fence_radius", 20)

            #if not mc.armed:
            #    mc.arm(wait=True)

            #mc.emergency_disarm(wait=True)
    except KeyboardInterrupt:
        print("exiting..")

    mc.close()
