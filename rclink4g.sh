#!/bin/bash

#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
BOOT_LOG_FILE="$LOG_DIR/boot.log"
DEFAULT_CONFIG_PATH="defaults/rclink4g.conf"
CONFIG_PATH="/boot/rclink4g.conf"
TAILSCALE_KEY=/boot/tailscale.key


function boot_log()
{
    MSG=$1
    ENTRY_TIMESTAMP=$(date +%H:%M:%S)
    echo "$ENTRY_TIMESTAMP: $MSG" | sudo tee -a "$BOOT_LOG_FILE"
}


function log()
{
    MSG=$1
    ENTRY_TIMESTAMP=$(date +%H:%M:%S)
    echo "$ENTRY_TIMESTAMP: $MSG" | sudo tee -a "$LOG_FILE"
}


function start_led_flash()
{
    GPIO="$1"
    ON="$2"
    OFF="$3"

    while true; do
	echo 1 | sudo tee /sys/class/gpio/gpio$GPIO/value &> /dev/null
	sleep $ON

	# allow always on (0 off time)
	if [[ "$OFF" != "0.0" && "$OFF" != "0" ]]; then
	    echo 0 | sudo tee /sys/class/gpio/gpio$GPIO/value &> /dev/null
	    sleep $OFF
	fi
    done
}

function stop_led_flash()
{
    FLASH_PID="$1"
    GPIO="$2"
    kill $FLASH_PID
    echo 0 | sudo tee /sys/class/gpio/gpio$GPIO/value &> /dev/null
}


function restart_script()
{
    log "restarting script.."
    exec "${BASH_SOURCE[0]}" $LOG_FILE
}


function kill_services()
{
    # kill webserver
    #log "killing webserver.."
    pkill althttpd

    # kill mavproxy
    #log "killing mavproxy.."
    pkill -f mavproxy

    # logout tailscale
    sudo tailscale logout
}


function start_video_streamer()
{
    # if video_streamer is not running
    if ! pkill -0 -f video_streamer.py &> /dev/null; then
        log "starting video streamer.."
        ./video_streamer.py &
    else
        # trigger video_streamer to reload it's config
        log "video_streamer reloading config.."
        pkill -hup -f video_streamer.py
    fi
}


function handle_exit()
{
    # stop video streamer
    log "stopping video streamer.."
    pkill -f video_streamer.py

    kill_services
    
    log "stopping rclink4g service.."
    exit
}


function handle_hup()
{
    log "configuration changed, restarting.."
    kill_services
    restart_script
}


function check_internet()
{
    TRIES=${1:-5}

    for i in $(seq 1 $TRIES); do
	#echo -n "trying to connect to quad9.net.. "
        if ping -c1 -W1.5 9.9.9.9 &> /dev/null && nc -zw1 www.quad9.net 443 &> /dev/null; then
	    #echo "success."
            return 0
        else
	    #echo "failure!"
            sleep 1
        fi
    done

    return 1
}


function connect_wifi()
{
    DEVICE="wlan0"
    OUTPUT_FILE="/etc/network/interfaces.d/$DEVICE"
    SSID="$1"
    PSK="$2"
    CURRENT_SSID=$(iwgetid -r)

    if [[ "$CURRENT_SSID" != "$SSID" ]]; then
        boot_log "connecting to $SSID.."
        sudo ifdown "$DEVICE" &> /dev/null
        echo "iface wlan0 inet dhcp" | sudo tee "$OUTPUT_FILE" &> /dev/null
        echo -e "\twpa-ssid\t$SSID" | sudo tee -a "$OUTPUT_FILE" &> /dev/null
        echo -e "\twpa-psk\t\t$PSK" | sudo tee -a "$OUTPUT_FILE" &> /dev/null
        sudo ifup "$DEVICE" &> /dev/null
    else
        boot_log "already connected to $SSID."
    fi
}


trap handle_exit EXIT
trap handle_hup HUP


# remove old boot log
sudo rm -f $BOOT_LOG_FILE


# change to script dir
cd "$SCRIPT_DIR"


# ensure config file exists and is non-empty or write default config
if [[ ! -s "$CONFIG_PATH" ]]; then
    boot_log "$CONFIG_PATH missing/empty, writing default config.."
    sudo cp "$DEFAULT_CONFIG_PATH" "$CONFIG_PATH"
else
    boot_log "found rclink4g config."
fi

# read the config file
source "$CONFIG_PATH"


# setup gpio
LED_PINS="18 23 24 25"

for LED_PIN in $LED_PINS; do
    echo $LED_PIN | sudo tee /sys/class/gpio/export &> /dev/null
    echo out | sudo tee /sys/class/gpio/gpio$LED_PIN/direction &> /dev/null
done



#========== connect to internet and update clock ==========
start_led_flash 18 0.01 1.0 &
FLASH_PID=$!

# connect to wireless network if specified/needed
if [[ -n "$wireless_ssid" && -n "$wireless_password" ]]; then
    connect_wifi "$wireless_ssid" "$wireless_password"
else
    boot_log "skipping wifi setup, no ssid/psk specified."
fi


# wait for internet connection to be established (if an advanced
# networking configuration is being used)
while ! check_internet; do
    sleep 1
done


# update clock
boot_log "updating clock.."
sudo ntpdate pool.ntp.org

stop_led_flash $FLASH_PID 18
#==========================================================



# create log file
LOG_FILE="${1:-$LOG_DIR/$(date +%s).log}"
sudo touch "$LOG_FILE"



#========== connect to tailscale (vpn) ==========
start_led_flash 23 0.01 1.0 &
FLASH_PID=$!

# connect to tailscale if needed
if ! tailscale status &> /dev/null; then
    log "connecting to tailscale.."

    if [[ ! -f "$TAILSCALE_KEY" ]]; then
        log "tailscale key not found!"
        stop_led_flash $FLASH_PID 23
	start_led_flash 23 0.01 0.2
    fi

    if sudo tailscale up --hostname "$hostname" --authkey file:"$TAILSCALE_KEY"; then
    	log "tailscale connected."
    else
        log "tailscale connection failed!"
        stop_led_flash $FLASH_PID 23
	start_led_flash 23 0.01 0.2
    fi
else
    log "already connected to tailscale."
fi

stop_led_flash $FLASH_PID 23
#================================================



# start video streamer (if needed)
start_video_streamer


# start webserver
#log "starting webserver.."
althttpd --root "$SCRIPT_DIR" --max-age 0 --port 8080 &> /dev/null &



#========== connect to the autopilot ==========
start_led_flash 24 0.01 1.0 &
FLASH_PID=$!

# start mavproxy
#log "starting mavproxy.."
if ping -q -c2 "$ground_station_address" &> /dev/null; then
    ./mavproxy.py --out "$ground_station_address":14550 --out 127.0.0.1:14551 --logfile=/tmp/mav.log --daemon &> /dev/null &

    #if (( $? != 0 )); then
    #    log "mavlink device /dev/ttyXXX not found!"
    #    flash_code 4 1
    #fi
else
    log "ground station $ground_station_address not reachable!"
fi

stop_led_flash $FLASH_PID 24
#==============================================



#========== monitor connectivity ==========
start_led_flash 25 0.01 1.0 &
FLASH_PID=$!

# periodically test internet connectivity
while check_internet; do
    sleep 1
done
log "lost internet connection!"

stop_led_flash $FLASH_PID 25
#==========================================



kill_services


# call custom script to handle resetting of comms
# hardware (cell modem, etc) if present
if [[ -f reset_network_link.sh ]]; then
    log "resetting network link"
    ./reset_network_link.sh
fi

restart_script
