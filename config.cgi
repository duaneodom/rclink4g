#!/bin/bash
source bash.cgi


#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
HTML_TEMPLATE_PATH="$SCRIPT_DIR/config.html"
CONFIG_PATH="/boot/rclink4g.conf"
source "$CONFIG_PATH"

#===== write out webpage html =====
echo -e "Content-type: text/html\n\n"
cat "$HTML_TEMPLATE_PATH" | sed \
    -e "s/<hostname>/$hostname/" \
    -e "s/<ground_station_address>/$ground_station_address/" \
    -e "s/<ground_station_video_port>/$ground_station_video_port/" \
    -e "s/<video_channel>/$video_channel/" \
    -e "/select.*video_stream_1/,/select/ s/value=\"$video_stream_1\"/value=\"$video_stream_1\" selected/" \
    -e "/select.*video_stream_2/,/select/ s/value=\"$video_stream_2\"/value=\"$video_stream_2\" selected/" \
    -e "/select.*video_stream_3/,/select/ s/value=\"$video_stream_3\"/value=\"$video_stream_3\" selected/" \
    -e "/select.*video_stream_4/,/select/ s/value=\"$video_stream_4\"/value=\"$video_stream_4\" selected/"
