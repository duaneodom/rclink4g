<h1 style="text-align: center">RCLink 4G</h1>

This project enables sending telemetry and video for ardupilot based vehicles
over a TCP/IP based connection (specifically cellular).  The hardware that has
been tested to work correctly so far is a Raspberry Pi Zero 2W, Raspberry Pi Camera
and a usb cellular dongle.  This hardware has been chosen for it's light weight,
compact size and low cost.



## Terms

- **Companion Computer**: Raspberry Pi
- **Camera**: Raspberry Pi Camera
- **GCS**: Ground Control Station (Mission Planner, QGroundControl, etc)
- **Mesh VPN**: Mesh Virtual Private Network (Tailscale specifically)
- **Autopilot**: ArduPilot compatible flight controller
- **Web Interface**: an HTML interface located on the companion computer accessible
via your web browser at http://hostname:8080 (hostname being the tailscale hostname
that you configured on the configuration settings page, default rclink4g)



## How it Works

The mesh VPN is used to make a connection between the cellular modem and your GCS.
Gstreamer running on the companion computer is used to stream video from the
camera to your GCS. The companion computer also runs mavproxy which provides a
TCP/IP based connection to your autopilot.  The companion computer also listens
to a user specified servo channel to allow you to change video resolutions,
framerates and to take high resolution snapshots. All of the user configurable
settings along with system logs and a snapshot library are available through
a web interface on the companion computer.



## Installation

I do not provide a Raspberry Pi image due to size limitations on github so instead
I provide a configuration script that will configure your installed Raspberry Pi
Lite OS (of the specified version) to be an RCLink4G companion computer. Once you
have your OS installed, login and run the following commands once connected to the
internet (replacing the file date/version info as appropriate).

```bash
curl -O -H "Accept: application/vnd.github.v3.raw" https://api.github.com/repos/duaneodom/rclink4g/contents/dist/setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
chmod +x setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
./setup_rclink4g_2023-05-03_bullseye_arm64_lite.run
```



## Tailscale Setup

As of now the only VPN supported is tailscale (this is likely to change in the
future), so to start things off you will need a free tailscale account.  The free
accounts give you up to 3 users and 100 devices (no subscription/credit card needed).
Tailscale is a mesh VPN.  This allows your devices to securely communicate with
each other over the open internet even through double NATs that are typical with
celluar providers.

- create your free tailscale account
- install the VPN software on your GCS and give it a memorable tailscale hostname
- create an ephemeral key to use on your RCLink4G unit
    - go to Admin Console -> Settings -> Keys
    - click Generate Auth Key
    - toggle reusable on
    - set expiration days (maximum preferred for convenience)
    - toggle ephemeral on
    - click Generate Key
    - copy the key text and paste it into a filed called tailscale.key



## RCLink4G Setup

Once you have successfully completed the Installation instructions above

1. copy your tailscale.key file to the root of the companion computer SD card
2. optionally edit **rclink4g.conf** file in the root of the SD card to change the following settings (see Configuration below for setting descriptions)
    - **hostname**
    - **ground_station_address**
    - **ground_station_video_port**
    - **video_channel**



## Boot Indicator LEDs

During the bootup of the companion computer each indicator LED will pulse once a
second during the stage indicated by the LED.  If a halting error occurs during
that stage, the LED will start a fast flash.  This tell you what stage failed
which should give you an indication of what the problem might be.  You can access
the logs in the logs directory on the root of the companion computer SD card for
more detailed information.  The boot stages are as follows

1. **network**: connecting to the internet and updating the clock
2. **vpn**: connecting to the mesh VPN (Tailscale)
3. **autopilot**: connecting via serial to the autopilot
4. **online**: the system is online

If the online LED turns off, this is an indication that internet/VPN connectivity
was lost.  The system will attempt to reset the internet connection, restart the connection
to the autopilot and restart the video streams.



## Configuration

All configuration settings are available via the web interface.

- **hostname**: the tailscale hostname that you want to give the companion computer
- **ground station address**: the tailscale hostname (or IP address) of your GCS
- **ground station video port**: the port at which your GCS is listening for a video stream
- **video channel**: the servo channel on the autopilot which you would like to
use for video switching
- **video stream PWM settings**: 4 PWM ranges for the selected video channel that
will select the configured video setting
    - none
    - very low bandwith
    - low bandwidth
    - normal bandwidth
    - high resolution snapshot



## Logs

Logs are accessible via the web interface and are split into Boot Logs and System Logs.

Boot Logs are things that occur before the companion computer has a connection to
the internet, as such, the timestamps for these logs will often be inaccurate.

System Logs are things that occur after the companion computer has a connection to
the internet and will tell you problems with things like: your mesh VPN, drops
in your internet connection, etc.



## Snapshot Library

Snapshots are accessible via the web interface.  All snapshots are named with a
timestamp and are located in one snapshot directory which is also accessible on
the root of the SD card on the companion computer.  You can download the snapshots
via the web interface or remove this SD card and insert it into your GCS computer
to have direct access to them.




*   when using picamera it is important to have mission planner (video player)
    running before starting the rclink4g unit.  this is due to some efficienies
    in video encoding that are taken when using the picamera on a lower power
    processor.
