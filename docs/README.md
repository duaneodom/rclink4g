<h1 style="text-align: center">RCLink 4G</h1>

This project enables sending telemetry and video for ardupilot based vehicles over a TCP/IP
connection (specifically cellular).  The hardware that has been tested to work correctly so far is a
Raspberry Pi 3B+/Zero 2W (others should work), a Raspberry Pi Camera, a USB camera, a usb cellular
dongle and standard WIFI using the Raspberry Pi built-in wireless chip.  This hardware has been
chosen for it's light weight, compact size and low cost.

![test hardware](docs/rclink4g.jpg "test hardware")



## Terms

- **Companion Computer**: Raspberry Pi
- **Camera**: Raspberry Pi Camera
- **GCS**: Mavlink based Ground Control Station (Mission Planner, QGroundControl, etc)
- **Mesh VPN**: Mesh Virtual Private Network (Tailscale specifically)
- **Autopilot**: ArduPilot compatible flight controller
- **Web Interface**: an HTML interface located on the companion computer accessible via your web
browser at `http://hostname:8080` (hostname being the tailscale hostname that you configured on the
configuration settings page, the default is "rclink4g")



## How it Works

The mesh VPN is used to make a connection between the companion computer and your GCS via the
cellular modem.  The companion computer streams video from the onboard camera to your GCS as well as
providing mavlink telemetry to your GCS all over the secure TCP/IP link provided by the cellular
modem and the mesh VPN.  The companion computer also listens to a user specified servo output to
allow you to change video resolutions, video framerates and to take high resolution snapshots from
your own RC transmitter. All of the user configurable settings along with the boot log, system logs
and a snapshot library are available through a web interface on the companion computer.



## Installation

I do not provide a Raspberry Pi image due to size limitations on github but instead provide a
configuration script that will configure your installed Raspberry Pi Lite OS to be an RCLink4G
companion computer. There are plenty of guides for installing Raspberry Pi OS online
([rpi-imager](https://www.raspberrypi.com/software/) is an easy tool) so I won't detail that process
here.  Once you have your OS installed and are connected to the internet, log in and run the
following commands (replacing the file date/version info as appropriate).

> **Note**
You must install the Raspberry Pi OS image that corresponds to the "date_codename_arch_lite" (eg.
2023-05-03_bullseye_arm64_lite) specified in the "setup_xxx_xxx_xxx_lite.run" filename.  Each
configuration script version is specifically built for **only** that version of the Raspberry Pi OS.

```bash
curl -O -H "Accept: application/vnd.github.v3.raw" https://api.github.com/repos/duaneodom/rclink4g/contents/dist/setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
chmod +x setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
./setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
```



## Official Raspberry Pi OS Image Links
[RPi OS Image 2023-05-03_bullseye_arm64_lite](https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2023-05-03/2023-05-03-raspios-bullseye-arm64-lite.img.xz)



## Tailscale Setup

As of now the only VPN supported is tailscale (this is likely to change in the future) so to start
things off you will need a free tailscale account.  The free accounts give you up to 3 users and 100
devices (no subscription/credit card needed).  Tailscale is a mesh VPN which allows your devices to
securely communicate with each other over the open internet even through double NATs that are
typical with celluar providers.

- create your free tailscale account at https://tailscale.com
- install the VPN software on your GCS and give it a tailscale hostname
- create an Auth Key to use on your RCLink4G unit
    - go to Admin Console -> Settings -> Keys
    - click Generate Auth Key
    - toggle reusable to on
    - set expiration days (maximum is preferred for convenience)
    - click Generate Key
    - copy the key text and paste it into a filed called tailscale.key



## RCLink4G Setup

Once you have successfully completed the [Installation](#installation) instructions above

1. copy your tailscale.key file to the root of the companion computer SD card
2. if desired, edit **rclink4g.conf** file in the root of the SD card to change the following
settings (see the [Configuration](#configuration) section below for setting descriptions). The other
settings should be filled in with the values you specified while running the installation script.
    - **ground_station_video_port**
    - **video_channel**
4. Start your GCS computer, connect to tailscale and start your GCS software
5. connect your RCLink4G to your autopilot via USB or serial cable
6. turn on your vehicle (which should also power on your RCLink4G unit)
7. wait for the telemetry and video stream to appear

> **Note**
When using a Raspberry Pi Camera it is important to have your GCS (video player) running before
starting the RCLink4G unit or the video stream won't show up.  This is due to some efficienies in
video encoding that are taken when using the Raspberry Pi Camera on the low power processor in the
Raspberry Pi Zero 2W.


## Boot Indicator LEDs

During the boot process of the companion computer each indicator LED will pulse once a second during
the stage indicated by the LED.  If a halting error occurs during that stage, the LED will start to
flash quickly and the boot process will be halted.  This will tell you what stage failed which
should give you an indication of what the problem might be.  You can access the logs in the logs
directory on the root of the companion computer SD card by removing it and inserting it into an SD
card reader on another computer (your GCS) for more detailed information.  The boot stages are as
follows

1. **network**: connecting to the internet and updating the system clock
2. **vpn**: connecting to the mesh VPN (Tailscale)
3. **autopilot**: connecting to the autopilot
4. **online**: the system is online

- If the online LED flashes quickly, this is an indication that the RCLink4G couldn't reach the GCS
address that you have defined in the [RCLink4G Setup](#rclink4g-setup) section.  Make sure the GCS
is connected to the internet and the mesh VPN (tailscale) and then click the restart button on the
web interface to retry the connection.

- If the online LED turns off, this is an indication that internet/VPN connectivity was lost.  The
system will attempt to reset the internet connection, reconnect to the autopilot and restart the
video streams.



## Configuration

All configuration settings are available via the web interface.

- **hostname**: the tailscale hostname that you want to assign to the companion computer
- **ground station address**: the tailscale hostname (or IP address) of your GCS
- **ground station video port**: the port at which your GCS is listening for a video stream. this
can also be in the form **address:port** if you want the video to be directed to a machine other
than the machine running your GCS software (large TV display, etc).
- **video servo**: the servo output on the autopilot which you would like to use for video
switching. This should be an unused servo output on your autopilot and you should setup your RC
transmitter to toggle this channel between the 4 fixed PWM ranges supported for the video servo.
- **wireless ssid**: the SSID (name) of the WiFi network that you want the RCLink4G to connect to.
- **wireless password**: the password for the WiFi network specified above.
- **video stream PWM settings**: the desired video setting for each of the 4 fixed PWM ranges for
the user configured video channel
    - none
    - very low bandwith
    - low bandwidth
    - normal bandwidth
    - high resolution snapshot



## Advanced Network Configuration

The default network configuration supports connecting to a WiFi hotspot/router via the rclink4g.conf
file on the root of the SD card as described in [RCLink4G Setup](#rclink4g-setup).  If you are
familiar with linux networking and wish to have an alternate/advanced network configuration you can
leave the **wireless_ssid** and **wireless_password** fields blank, mount the second partition of
the SD card on another computer (eg. your GCS) and configure the network to your liking.  The only
requirements of the network connection are that it comes up automatically upon boot, it results in a
connection to the internet and it doesn't prevent the mesh VPN (tailscale) establishing a
connection.



## Logs

Logs are accessible via the web interface and are split into the Boot Log and System Logs.

The Boot Log contains things that occur before the companion computer has a connection to the
internet. Because of this the timestamps for these logs will often be inaccurate. This log is useful
for determining problems with things such as:

- invalid `rclink4g.conf` config file
- problems connecting to the internet
- problems updating the system clock

System Logs are things that occur after the companion computer has a connection to the internet and
will have accurately timestamped entries for things such as:

- Mesh VPN key problems
- Mesh VPN successful/failed connections
- service restarts due to configuration changes (when a restart is required)
- service restarts due to drops in internet connectivity




## Snapshot Library

The high resolution snaphots that you take are accessible via the web interface.  All snapshots are
named with a timestamp and are located in the snapshot directory which is also accessible on the
root of the SD card on the companion computer.  You can download the snapshots via the web interface
or remove this SD card and insert it into your GCS computer to have direct access to them.

> **Warning**
The default boot partition (the drive that shows up when you insert the SD card into a windows
computer) is only about 250Mb in size.  This limits the number of high resolution snapshots that you
can take without running out of free space.  If you are and advanced user you can follow the
instructions HERE to resize this partition to be larger.

> **Warning**
Although you can download these snapshots via the web interface, it is suggested to wait until you
are no longer actively operating your vehicle as this might saturate the bandwidth of your
cellular/wireless connection and hinder the operation of your vehicle.  This can also use lots of
costly data on metered connections such as cellular.  A better alternative is to pull the SD card
out of the RCLink4G unit and insert it into an SD card reader on another computer (your GCS) to copy
the snapshots over directly.




## Mission Planner Joystick Setup

Because of the long distances at which this device can be used, it is likely that your traditional
RC transmitter will not be able to maintain connectivity to your vehicle. For this reason, if your
vehicle is not fully autonomous you will want to use a joystick/gamepad through your GCS to do any
manual control. To set this up, first follow the tutorials on the Mission Planner website to
setup/calibrate your joystick in Windows. Next, you will need to setup a joystick button to activate
each of the video stream ranges that you plan to use (up to 4). Follow the procedure below.

- go to Setup -> Optional Hardware -> Joystick
- disable the joystick (if it is enabled)
- setup the first video stream activation button
    1. click the Detect button associated with But1 and click Ok on the resulting dialog
    2. press and release the button on the controller you want to associate with But1
    3. change the action in the drop-down associated with But1 to Do_Set_Servo
    4. click the Settings button associated with But1
    5. change the Servo setting to the servo number specified in the video_servo setting (eg. 8).
    6. change the PWM value to 1100
    7. close the Settings window for But1
- repeat these steps for every video stream activation button you plan to use by changing the But1
and the PWM value (eg. But2,But3,But4 and 1300,1600,1800).
- click the Save button to save your joystick setup
- click the Enable button to start using the joystick input again

> **Note**
To verify that your Do_Set_Servo commands are actually happening on the autopilot you can go to the
Data screen on Mission Planner, enable the Tuning checkbox at the bottom of the screen, double-click
the graph that appears and select to show the servo channel for the video_servo that you configured
(eg. ch8_out), close the settings window and press the joystick buttons you defined in the previous
steps.  You should see the PWM values on the graph changing for the selected servo channel (eg.
ch8_out) to the values you configured in the previous steps (eg. 1100,1300,1600,1800).


## Troubleshooting

- If you cannot access your RCLink4G device via the hostname you specified on the Tailscale network
it might be because a stale device connection may have existed on your Tailscale network when you
were making the connection.  In this case Tailscale tacks on a "-1, -2, etc" to the name your
specified to prevent name clashes (eg, you specify "xyz") and it shows up as "xyz-1").
To fix this you will need to shut down your RCLink4G, remove all machines with the specified name
from your Tailscale network ("xyz", "xyz-1", "xyz-2"), copy your tailscale.key to to root of your
RCLink4G SD card.  When you boot the RCLink4G again, it should reconnect to the Tailscale network
with the correct name.
