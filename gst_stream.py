#!/usr/bin/env python3
import os
import time
import subprocess
import shlex
import re



ADDR = 0
PORT = 1
REQ_RES = 2
RES = 3
FPS = 4




class gst_stream:
    def __init__(self, title, video_cmd, stream_cmd, record_cmd=None, snapshot_cmd=None):
        self.title = title
        self.video_cmd = video_cmd
        self.stream_cmd = stream_cmd
        self.record_cmd = record_cmd
        self.snapshot_cmd = snapshot_cmd
        self.recording = False
        self.recording_location = None
        self.proc_handle = None
        self.DEVNULL = open(os.devnull, "w")

        self.res = (int(re.findall("width=(\d+)",self.video_cmd)[0]), int(re.findall("height=(\d+)",self.video_cmd)[0]))

        #=== client structure ===
        # [address, port, requested_res, actual_res, fps]
        # eg. [ "192.168.1.9", 5000, (1600x1200), (320,240), 10]
        self.clients = []

        print(f"{self.title} stream created.")



    def close(self):
        if self.clients:
            print(f"{self.title} stream closing..")

        self.stop()
        self.DEVNULL.close()



    def add_client(self, client, res=None, fps=None):
        address,port = client
        req_res, res = self._parse_res(res)
        client = [address, port, req_res, res, fps]

        if not self._is_duplicate_client(client):
            self.stop()
            self.clients.append(client)
            self.start()
        else:
            print(f"not adding duplicate client ({address},{port})")



    def has_client_stream(self, address, resolution, fps):
        c2 = [address[0], address[1], resolution, None, fps]
        
        for c1 in self.clients:
            # if clients have the same address, port, requested_res and fps
            if c1[:3] == c2[:3] and c[4] == c2[4]:
                return True
        
        return False



    def remove_client(self, client, res=None, fps=None):
        address,port = client
        req_res, res = self._parse_res(res)
        client = [address, port, req_res, res, fps]

        if client in self.clients:
            self.stop()
            self.clients.remove(client)

            # if there are still clients to serve then start again
            if self.clients:
                self.start()



    def remove_all_clients(self):
        self.stop()
        self.clients = []
        self.start()



    def cleanup_client(self, address):
        need_to_restart = False

        # loop thru clients removing any that have a matching address
        for client in self.clients:
            if client[ADDR] == address:
                self.clients.remove(client)
                need_to_restart = True

        # if we need to restart bc the client list changed then
        # stop the stream and start it again if there are clients remaining
        if need_to_restart:
            self.stop()

            if self.clients:
                self.start()



    def start(self):
        if self.proc_handle is None:
            if self.clients:
                process_cmd = f"{self.video_cmd} ! tee name=t "

                # collect all native feed clients and a list of the custom feeds needed
                native_feed_clients = []        # list of (addr,port) pairs
                custom_feeds = {}               # dict of lists of (addr,port) pairs keyed by (res,fps) pairs

                for client in self.clients:
                    if (client[RES] == self.res or client[RES] is None) and client[FPS] is None:
                        native_feed_clients.append((client[ADDR],client[PORT]))
                    else:
                        custom_feed_id = (client[RES],client[FPS])

                        if custom_feed_id in custom_feeds:
                            custom_feeds[custom_feed_id].append((client[ADDR],client[PORT]))
                        else:
                            custom_feeds[custom_feed_id] = [(client[ADDR],client[PORT])]

                #print(f"\nnative clients:\n{native_feed_clients}")
                #print(f"custom clients:\n{custom_feeds}\n")

                if native_feed_clients:
                    native_feed_clients_string = ",".join([f"{x[0]}:{x[1]}" for x in native_feed_clients])

                    # add native feed clients pipeline to the process_cmd
                    native_feed_clients_cmd = f"t. ! queue ! {self.stream_cmd} "
                    native_feed_clients_cmd = native_feed_clients_cmd.replace("clients=", f"clients={native_feed_clients_string}")
                    process_cmd += native_feed_clients_cmd

                # loop thru all custom feeds building the scale/encode pipeline for each one with the
                # interested clients list, then append this pipeline to the process_cmd
                for res,fps in custom_feeds:
                    custom_feed_clients_string = ",".join([f"{x[0]}:{x[1]}" for x in custom_feeds[(res,fps)]])
                    custom_feed_clients_cmd = "t. ! queue ! "

                    if custom_feed_clients_string:
                        if res:
                            custom_feed_clients_cmd += "videoscale ! "

                        if fps:
                            custom_feed_clients_cmd += "videorate ! "

                        custom_feed_clients_cmd += "video/x-raw"

                        if res:
                            custom_feed_clients_cmd += ",width=,height="

                        if fps:
                            custom_feed_clients_cmd += ",framerate="


                        custom_feed_clients_stream_cmd = self.stream_cmd

                        if fps:
                            # ensure a keyrame once a second for the specified fps
                            custom_feed_clients_stream_cmd = re.sub("key-int-max=\d+", f"key-int-max={fps}", custom_feed_clients_stream_cmd)
                            custom_feed_clients_stream_cmd = re.sub("interval-intraframes=\d+", f"interval-intraframes={fps}", custom_feed_clients_stream_cmd)

                        custom_feed_clients_cmd += f" ! {custom_feed_clients_stream_cmd} "
                        custom_feed_clients_cmd = custom_feed_clients_cmd.replace("clients=", f"clients={custom_feed_clients_string}")

                        if res:
                            custom_feed_clients_cmd = custom_feed_clients_cmd.replace("width=", f"width={res[0]}")
                            custom_feed_clients_cmd = custom_feed_clients_cmd.replace("height=", f"height={res[1]}")
                        
                        if fps:
                            custom_feed_clients_cmd = custom_feed_clients_cmd.replace("framerate=", f"framerate={fps}/1")

                        process_cmd += custom_feed_clients_cmd

                # if we are recording, add the record_cmd to the process_cmd
                if self.recording and self.recording_location:
                    recording_cmd = f"t. ! queue ! {self.record_cmd} "
                    recording_cmd = recording_cmd.replace("location=", f"location={self.recording_location}")
                    process_cmd += recording_cmd

                try:
                    print(f"starting video feed: {process_cmd}")
                    self.proc_handle = subprocess.Popen(shlex.split(process_cmd), stdout=self.DEVNULL, stderr=self.DEVNULL)
                except:
                    print("failed to start stream command!")
            else:
                print("no clients to serve!")
        else:
            print("stream already running!")



    def stop(self):
        if not self.proc_handle is None:
            #print("stopping video feed..")

            #print("killing proc..")
            self.proc_handle.kill()
            #print("waiting on proc..")
            self.proc_handle.wait()
            #print("deleting proc..")
            self.proc_handle = None



    def start_recording(self, filepath="", stop=False):
        response = False

        if self.record_cmd:
            was_running = (not self.proc_handle is None)

            if was_running:
                self.stop()

            if stop:
                self.recording_location = None
                self.recording = False
            else:
                self.recording_location = filepath
                self.recording = True

            if was_running:
                self.start()

            response = True

        return response

    def stop_recording(self):
        self.start_recording(stop=True)



    def snapshot(self, resolution, filepath):
        response = False

        if self.snapshot_cmd:
            try:
                cmd = self.snapshot_cmd
                
                # only replace the width and height specifiers if the snapshot
                # command didn't give a hard specifier for width and height
                snapshot_res_hard_spec =  re.findall("width=(\d+)",self.snapshot_cmd) and re.findall("height=(\d+)",self.snapshot_cmd)

                if not snapshot_res_hard_spec:
                    width,height = (int(x) for x in resolution.split("x"))
                    cmd = cmd.replace("width=", f"width={width}")
                    cmd = cmd.replace("height=", f"height={height}")

                cmd = cmd.replace("location=", f"location={filepath}")

                was_running = (not self.proc_handle is None)

                if was_running:
                    self.stop()

                try:
                    #print(f"taking a snapshot with cmd: {cmd}")
                    subprocess.check_call(shlex.split(cmd), stdout=self.DEVNULL, stderr=self.DEVNULL)
                except Exception as e:
                    print("exception calling snapshot command!")
                    print(e)

                if was_running:
                    self.start()

                response = True
            except:
                print("failed to take snapshot!")

        return response



    def _parse_res(self, requested_res):
        actual_res = None

        try:
            w,h = [int(x) for x in requested_res.split("x")]
            
            # if a larger res was requested, then default to native res (None)
            if w >= self.res[0]:
                actual_res = None
            else:
                actual_res = (w,h)
        # fail over to native res (None)
        except AttributeError:
            actual_res = None

        return (requested_res, actual_res)



    def _is_duplicate_client(self, client):
        # this test is for making sure that we arent trying to send
        # ANY video stream to the same address/port combination
        # regardless of varying resolutions/fps
        for c in self.clients:
            # clients have the same address and port
            if c[:2] == client[:2]:
                return True
        
        return False






if __name__ == "__main__":
    #=== example resulting gst-launch command line ===
    # gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480 ! videoconvert ! tee name=t
    # t. ! queue ! x264enc speed-preset=ultrafast tune=zerolatency key-int-max=15 ! rtph264pay ! udpsink clients=127.0.0.1:5000
    # t. ! queue ! videoscale ! videorate ! video/x-raw,width=160,height=120,framerate=2/1 ! x264enc speed-preset=ultrafast tune=zerolatency key-int-max=2 ! rtph264pay ! udpsink clients=127.0.0.1:5001

    # the stream command pulls the frames from the sensor and determines the "native" resolution of the
    # stream.  all custom streams will be the same resolution or smaller. caution should be used with
    # requesting alternate resolutions and frame rates bc this puts extra processing load on the streamer

    #=== laptop testing ===
    video_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480 ! videoconvert"
    stream_cmd = "x264enc speed-preset=ultrafast tune=zerolatency key-int-max=15 ! rtph264pay ! udpsink clients="
    record_cmd = "x264enc speed-preset=ultrafast tune=zerolatency key-int-max=15 ! filesink location="
    snapshot_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! image/jpeg,width=,height= ! filesink location="

    #=== picamera very efficient ===
    #video_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-h264,width=640,height=480,framerate=15/1 ! h264parse"
    #stream_cmd = "rtph264pay ! udpsink clients="
    #record_cmd = "avimux ! filesink location="
    #snapshot_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! image/jpeg,width=,height= ! filesink location="

    #=== usb camera best i could get, but pretty heavy ===
    #video_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 ! videorate ! video/x-raw,width=640,height=480,framerate=15/1 ! videoconvert"
    #stream_cmd = "v4l2h264enc extra-controls=controls,video_bitrate=1000000,h264_i_frame_period=15 ! 'video/x-h264,level=(string)3' ! rtph264pay ! udpsink clients="
    #record_cmd = "v4l2h264enc extra-controls=controls,video_bitrate=1000000,h264_i_frame_period=15 ! 'video/x-h264,level=(string)3' ! avimux ! filesink location="
    #snapshot_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! image/jpeg,width=,height= ! filesink location="
    
    #=== scratch examples to play with ===
    #video_cmd = "gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg,width=640,height=480 ! jpegdec ! videoconvert"
    #stream_cmd = "omxh264enc interval-intraframes=15 ! rtph264pay ! udpsink clients="
    #record_cmd = ""
    #snapshot_cmd = ""

    #===== test player commands =====
    #gst-launch-1.0 udpsrc port=5000 ! application/x-rtp ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
    #gst-launch-1.0 udpsrc port=5001 ! application/x-rtp ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
    
    s = gst_stream("test stream", video_cmd, stream_cmd, record_cmd, snapshot_cmd)
    s.start()

    print("adding native client..")
    s.add_client( ("127.0.0.1",5000) )

    #print("adding another native client..")
    #s.add_client( ("127.0.0.2",5000) )

    time.sleep(10.0)

    #print("adding alternate framerate client..")
    #s.add_client( ("127.0.0.2",5001), fps=8)
    #s.add_client("127.0.0.3", 5000, res="1600x1200")
    
    print("adding alternate resolution client..")
    s.add_client( ("127.0.0.1",5001), res="160x120")

    #print("adding alternate framerate and resolution client..")
    #s.add_client( ("127.0.0.1",5001), res="160x120", fps=2)

    time.sleep(10.0)

    #print("starting recording..")
    #s.start_recording("test.avi")
    #time.sleep(5.0)
    #s.snapshot("1920x1080", "test.jpg")
    #time.sleep(5.0)
    #print("stopping recording..")
    #s.stop_recording()


    #print("adding alternate framerate and invalid resolution client..")
    #s.add_client( ("127.0.0.2",5004), res="1600x1200", fps=1)

#    print(f"clients: {s.clients}")
#    time.sleep(10.0)

    # remove and re-add client while running to verify functionality
#    print("removing client..")
#    s.remove_client( ("127.0.0.1",5000) )
    #s.remove_client("127.0.0.2", 5000, fps=8)
    #s.remove_client("127.0.0.3", 5000, res="1600x1200")
#    s.remove_client( ("127.0.0.1",5001), res="320x240")
    #print(s.clients)
#    time.sleep(2.0)
#    print("adding client..")
#    s.add_client(("127.0.0.1",5000))
#    time.sleep(3.0)

    # stop and restart client to verify previously added clients remain
#    s.stop()
#    time.sleep(2.0)
#    s.start()
#    time.sleep(3.0)

    # test snapshot capability
#    s.snapshot("1280x720", "/tmp/test.jpg")
#    time.sleep(3.0)

    s.stop()
