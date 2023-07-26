#!/bin/bash
source bash.cgi


#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
CONFIG_PATH="/boot/rclink4g.conf"
hostname=${FORMS[hostname]}
ground_station_address=${FORMS[ground_station_address]}
ground_station_video_port=${FORMS[ground_station_video_port]}
video_channel=${FORMS[video_channel]}
video_stream_1=${FORMS[video_stream_1]}
video_stream_2=${FORMS[video_stream_2]}
video_stream_3=${FORMS[video_stream_3]}
video_stream_4=${FORMS[video_stream_4]}


#===== write new config values to config file =====
sudo -- bash -c '
sed -i "s/hostname=.*/hostname=$hostname/" "$CONFIG_PATH"
sed -i "s/ground_station_address=.*/ground_station_address=$ground_station_address/" "$CONFIG_PATH"
sed -i "s/ground_station_video_port=.*/ground_station_video_port=$ground_station_video_port/" "$CONFIG_PATH"
sed -i "s/video_channel=.*/video_channel=$video_channel/" "$CONFIG_PATH"
sed -i "s/video_stream_1=.*/video_stream_1=$video_stream_1/" "$CONFIG_PATH"
sed -i "s/video_stream_2=.*/video_stream_2=$video_stream_2/" "$CONFIG_PATH"
sed -i "s/video_stream_3=.*/video_stream_3=$video_stream_3/" "$CONFIG_PATH"
sed -i "s/video_stream_4=.*/video_stream_4=$video_stream_4/" "$CONFIG_PATH"
'


echo "<!DOCTYPE html>
<html>
   <head>
       <meta http-equiv=\"refresh\" content=\"5; url='/config.cgi'\" />
   </head>
   <body>
       <p>Settings saved. please wait 5 seconds for service restart and page reload..</p>
       <p>If page doesn't reload automatically, click <a href=\"/config.cgi\">here</a>.</p>
   </body>
</html>"

pkill -hup -f rclink4g.sh
