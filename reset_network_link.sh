#!/bin/bash

# if connected via USB cell modem, then reset
# cell modem by cycling USB power
if ip link show usb0 &> /dev/null; then
    #sudo uhubctl -l 1-1 -p 2 -a off
    sleep 3
    #sudo uhubctl -l 1-1 -p 2 -a on
fi

# wait for cell connection
sleep 15
