<h1 style="text-align: center">RCLink 4G</h1>

This project enables sending telemetry and video for ardupilot based vehicles
over a TCP/IP connection (specifically cellular).  The hardware that has been
tested to work correctly so far is a Raspberry Pi 3B+/Zero 2W (others should
work), a Raspberry Pi Camera, a USB camera, a usb cellular dongle and standard
WIFI using the Raspberry Pi built-in wireless chip.  This hardware has been
chosen for it's light weight, compact size and low cost.

![test hardware](docs/rclink4g.jpg "test hardware")



## Terms

- **Companion Computer**: Raspberry Pi
- **Camera**: Raspberry Pi Camera
- **GCS**: Mavlink based Ground Control Station (Mission Planner, QGroundControl, etc)
- **Mesh VPN**: Mesh Virtual Private Network (Tailscale specifically)
- **Autopilot**: ArduPilot compatible flight controller
- **Web Interface**: an HTML interface located on the companion computer accessible
via your web browser at `http://hostname:8080` (hostname being the tailscale hostname
that you configured on the configuration settings page, the default is "rclink4g")



## How it Works

The mesh VPN is used to make a connection between the companion computer and your GCS
via the cellular modem.  The companion computer streams video from the onboard
camera to your GCS as well as providing mavlink telemetry to your GCS all over the
secure TCP/IP link provided by the cellular modem and the mesh VPN.  The companion
computer also listens to a user specified servo channel to allow you to change video
resolutions, video framerates and to take high resolution snapshots from your own
RC transmitter. All of the user configurable settings along with system logs and a
snapshot library are available through a web interface on the companion computer.



## Installation

I do not provide a Raspberry Pi image due to size limitations on github but instead
provide a configuration script that will configure your installed Raspberry Pi
Lite OS to be an RCLink4G companion computer. There are plenty of guides for installing
Raspberry Pi OS online ([rpi-imager](https://www.raspberrypi.com/software/) is an easy tool)
so I won't detail that process here.  Once you have your OS installed and are connected
to the internet, log in and run the following commands (replacing the file date/version
info as appropriate).

> **Note**
You must install the Raspberry Pi OS image that corresponds to the
"date_codename_arch_lite" (eg. 2023-05-03_bullseye_arm64_lite) specified in the
"setup_xxx_xxx_xxx_lite.run" filename.  Each configuration script version is
specifically built for **only** that version of the Raspberry Pi OS.

```bash
curl -O -H "Accept: application/vnd.github.v3.raw" https://api.github.com/repos/duaneodom/rclink4g/contents/dist/setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
chmod +x setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
./setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
```



## Official Raspberry Pi OS Image Links
[RPi OS Image 2023-05-03_bullseye_arm64_lite](https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2023-05-03/2023-05-03-raspios-bullseye-arm64-lite.img.xz)



## Tailscale Setup

As of now the only VPN supported is tailscale (this is likely to change in the
future) so to start things off you will need a free tailscale account.  The free
accounts give you up to 3 users and 100 devices (no subscription/credit card needed).
Tailscale is a mesh VPN which allows your devices to securely communicate with
each other over the open internet even through double NATs that are typical with
celluar providers.

- create your free tailscale account at https://tailscale.com
- install the VPN software on your GCS and give it a tailscale hostname
- create an ephemeral key to use on your RCLink4G unit
    - go to Admin Console -> Settings -> Keys
    - click Generate Auth Key
    - toggle reusable to on
    - set expiration days (maximum is preferred for convenience)
    - toggle ephemeral to on
    - click Generate Key
    - copy the key text and paste it into a filed called tailscale.key



## RCLink4G Setup

Once you have successfully completed the [Installation](#installation) instructions above

1. copy your tailscale.key file to the root of the companion computer SD card
2. edit **rclink4g.conf** file in the root of the SD card to change the following
settings (see the [Configuration](#configuration) section below for setting descriptions)
    - _Recommended/Necessary_
        - **ground_station_address**
        - **wireless_ssid**
        - **wireless_password**
    - _Optional_
        - **hostname**
        - **ground_station_video_port**
        - **video_channel**
4. Start your GCS computer, connect to tailscale and start your GCS software
5. connect your RCLink4G to your autopilot via USB or serial cable
6. turn on your vehicle (which powers on your RCLink4G unit)
7. wait for the telemetry and video stream to appear

> **Note**
When using a Raspberry Pi Camera it is important to have your GCS (video player) running
before starting the RCLink4G unit or the video stream won't show up.  This is due to
some efficienies in video encoding that are taken when using the Raspberry Pi Camera
on the low power processor in the Raspberry Pi Zero 2W.


## Boot Indicator LEDs

During the boot process of the companion computer each indicator LED will pulse once a
second during the stage indicated by the LED.  If a halting error occurs during
that stage, the LED will start to flash quickly and the boot process will be halted.
This will tell you what stage failed which should give you an indication of what the
problem might be.  You can access the logs in the logs directory on the root of the
companion computer SD card by removing it and inserting it into an SD card reader on
another computer (your GCS) for more detailed information.  The boot stages are as follows

1. **network**: connecting to the internet and updating the clock
2. **vpn**: connecting to the mesh VPN (Tailscale)
3. **autopilot**: connecting to the autopilot
4. **online**: the system is online

If the online LED flashes quickly, this is an indication that the RCLink4G couldn't reach
the GCS address that you have defined in the [RCLink4G Setup](#rclink4g-setup) section.
Make sure the GCS is connected to the internet and the mesh VPN (tailscale) and then click
the restart button on the web interface to retry the connection.  If the online LED turns
off, this is an indication that internet/VPN connectivity was lost.  The system will
attempt to reset the internet connection, reconnect to the autopilot and restart the
video streams.



## Configuration

All configuration settings are available via the web interface.

- **hostname**: the tailscale hostname that you want to assign to the companion computer
- **ground station address**: the tailscale hostname (or IP address) of your GCS
- **ground station video port**: the port at which your GCS is listening for a video stream
- **video channel**: the servo channel on the autopilot which you would like to
use for video switching. This should be an unused servo channel on your autopilot and
you should setup your RC transmitter to toggle this channel between the 4 fixed PWM ranges
supported for the video channel.
- **wireless ssid**: the SSID (name) of the WiFi network that you want the RCLink4G to connect to.
- **wireless password**: the password for the WiFi network specified above.
- **video stream PWM settings**: the desired video setting for each of the 4 fixed PWM ranges
for the user configured video channel
    - none
    - very low bandwith
    - low bandwidth
    - normal bandwidth
    - high resolution snapshot



## Advanced Network Configuration

The default network configuration supports connecting to a WiFi hotspot/router via the
rclink4g.conf file on the root of the SD card as described in [RCLink4G Setup](#rclink4g-setup).
If you are familiar with linux networking and wish to have an alternate/advanced network
configuration you can leave the **wireless_ssid** and **wireless_password** fields blank,
mount the second partition of the SD card on another computer (eg. your GCS) and configure the
network to your liking.  The only requirements of the network connection are that it comes up
automatically upon boot, it results in a connection to the internet and it doesn't prevent
the mesh VPN (tailscale) establishing a connection.



## Logs

Logs are accessible via the web interface and are split into Boot Logs and System Logs.

Boot Logs are things that occur before the companion computer has a connection to
the internet, as such, the timestamps for these logs will often be inaccurate.  This log
is useful for determining problems with things such as:

- invalid `rclink4g.conf` config file
- problems connecting to the internet
- problems updating the clock

System Logs are things that occur after the companion computer has a connection to
the internet and will have accurately timestamped entries for things such as:

- Mesh VPN key problems
- Mesh VPN successful/failed connections
- service restarts due to configuration changes (when a restart is required)
- service restarts due to drops in internet connectivity




## Snapshot Library

The high resolution snaphots that you take are accessible via the web interface.  All
snapshots are named with a timestamp and are located in the snapshot directory which
is also accessible on the root of the SD card on the companion computer.  You can
download the snapshots via the web interface or remove this SD card and insert it into
your GCS computer to have direct access to them.

> **Warning**
Although you can download these snapshots via the web interface, it is suggested to wait
until you are no longer actively operating your vehicle as this might saturate the
bandwidth of your cellular/wireless connection and hinder the operation of your vehicle.
This can also use lots of costly data on metered connections such as cellular.  A better
alternative is to pull the SD card out of the RCLink4G unit and insert it into an SD card
reader on another computer (your GCS) to copy the snapshots over directly.
