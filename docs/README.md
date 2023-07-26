<h1 style="text-align: center">RCLink 4G</h1>
________________________________________________________________________________

This project enables sending telemetry and video for ardupilot based vehicles
over a TCP/IP based connection (specifically cellular).  The hardware that has
been tested to work correctly so far is a Raspberry Pi Zero 2W, Raspberry Pi Camera
and a usb cellular dongle.  This hardware has been chosen for it's light weight,
compact size and low cost.

## Terms
________________________________________________________________________________

- **Companion Computer**: Raspberry Pi
- **Camera**: Raspberry Pi Camera
- **GCS**: Ground Control Station (Mission Planner, QGroundControl, etc)
- **Mesh VPN**: Mesh Virtual Private Network (Tailscale specifically)
- **Autopilot**: ArduPilot compatible flight controller
- **Web Interface**: an HTML interface located on the companion computer accessible
via your web browser at http://hostname:8080 (hostname being the tailscale hostname
that you configured on the configuration settings page, default rclink4g)


## How it Works
________________________________________________________________________________

The mesh VPN is used to make a connection between the cellular modem and your GCS.
Gstreamer running on the companion computer is used to stream video from the
camera to your GCS. The companion computer also runs mavproxy which provides a
TCP/IP based connection to your autopilot.  The companion computer also listens
to a user specified servo channel to allow you to change video resolutions,
framerates and to take high resolution snapshots. All of the user configurable
settings along with system logs and a snapshot library are available through
a web interface on the companion computer.


## Configuration
________________________________________________________________________________

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
________________________________________________________________________________

Logs are accessible via the web interface and are split into Boot Logs and System Logs.

Boot Logs are things that occur before the companion computer has a connection to
the internet, as such, the timestamps for these logs will often be inaccurate.

System Logs are things that occur after the companion computer has a connection to
the internet and will tell you problems with things like: your mesh VPN, drops
in your internet connection, etc.

## Snapshot Library
________________________________________________________________________________

Snapshots are accessible via the web interface.  All snapshots are named with a
timestamp and are located in one snapshot directory which is also accessible on
the root of the SD card on the companion computer.  You can download the snapshots
via the web interface or remove this SD card and insert it into your GCS computer
to have direct access to them.


## Installation
________________________________________________________________________________

I do not provide a Raspberry Pi image due to size limitations on github so instead
I provide a configuration script that will configure your installed Raspberry Pi
Lite OS (of the specified version) to be an RCLink4G companion computer. Once you
have your OS installed, you run the following commands

```bash
curl -s http://github.com/duaneodom/rclink4g/setup_rclink4g.run
chmod +x setup_rclink4g.run
./setup_rclink4g.run
```

## Tailscale Setup
________________________________________________________________________________

1. create a tailscale account
2. setup tailscale on your GCS
3. create a tailscale ephemeral key
4. save your ephemeral key into a file called tailscale.key

## RCLink4G Setup
________________________________________________________________________________

Once you have successfully completed the Installation instructions

1. copy your tailscale.key file to the root of the companion computer SD card

## Boot Indicator LEDs
________________________________________________________________________________

Each indicator LED will pulse once a second during the boot stage indicated by
the LED.  If a halting error occurs during that stage, the LED will start
a fast flash.  This tell you what stage failed which should give you an indication
of what the problem might be.  You can access the logs in the logs directory on
the root of the companion computer SD card for more detailed information.

1. **network**: connecting to the internet and updating the clock
2. **vpn**: connecting to the mesh VPN (Tailscale)
3. **autopilot**: connecting via serial to the autopilot
4. **online**: the system is online

If the online LED turns off, this is an indication that internet/VPN connectivity
was lost.  The system will attempt to reset the connection, restart the connection
to the autopilot and restart the video streams.




*   when using picamera it is important to have mission planner (video player)
    running before starting the rclink4g unit.  this is due to some efficienies
    in video encoding that are taken when using the picamera on a lower power
    processor.
