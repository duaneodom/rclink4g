#!/bin/bash

#===== run the following command on target machine =====
# bash -c "$(curl -s http://10.10.1.3:8080/setup_rclink4g.run)"



spinner()
{
    WAIT_PID=$1
    SPINNER="◢◣◤◥"

    # hide cursor
    tput civis

    while kill -0 $WAIT_PID 2>/dev/null; do
        for (( i=0; i<${#SPINNER}; i++ )); do
            sleep 0.2
            echo -en "${SPINNER:$i:1}\b"
        done
    done

    # clear spinner
    echo -en " \b"

    # restore cursor
    tput cnorm
}



echo
read -p "This will convert your Raspberry Pi OS install to RCLink4G. Are you sure you want to continue? <y/N> " PROMPT
echo

if [[ $PROMPT =~ [yY].* ]]; then
    echo "disabling bluetooth.."
    grep -q "^dtoverlay=disable-bt" /boot/config.txt &> /dev/null || sudo sh -c "echo dtoverlay=disable-bt >> /boot/config.txt"


    echo "removing boot delay.."
    grep "^boot_delay=0" /boot/config.txt &> /dev/null || sudo sh -c "echo boot_delay=0 >> /boot/config.txt"


    echo "disabling splash screen.."
    grep "^disable_splash=1" /boot/config.txt &> /dev/null || sudo sh -c "echo disable_splash=1 >> /boot/config.txt"


    echo "configuring gpu memory.."
    sudo raspi-config nonint do_memory_split 256


    echo "configuring legacy camera support.."
    sudo raspi-config nonint do_legacy 0


    echo "silencing login.."
    touch /home/pi/.hushlogin
    sudo sh -c "echo -n > /etc/issue"
    sudo sh -c "echo -n > /etc/motd"
    sudo rm -f /etc/profile.d/sshpwd.sh
    sudo sed -e 's/^#*/#/' -i /etc/rc.local


    ## generate password hash for userconf.txt with following command
    ## echo 'mypassword' | openssl passwd -6 -stdin
    #echo "setting up account.."
    #sudo cp files/userconf.txt /boot


    # not needed if systemd-timesyncd is running
    #echo "updating clock.."
    #sudo ntpdate pool.ntp.org


    echo -n "removing dhcpcd/network-manager "
    sudo apt -y remove --purge dhcpcd5 network-manager &> /dev/null &
    spinner $!
    echo


    echo "installing tailscale keys.."
    curl -fsSL https://pkgs.tailscale.com/stable/raspbian/$(lsb_release -sc).noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg > /dev/null
    sudo chmod 644 /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL https://pkgs.tailscale.com/stable/raspbian/$(lsb_release -sc).tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list > /dev/null
    sudo chmod 644 /etc/apt/sources.list.d/tailscale.list


    echo -n "updating system "
    sudo sh -c "apt update && apt -y upgrade && apt -y autoremove && apt -y autoclean" &> /dev/null &
    spinner $!
    echo


    echo -n "installing packages "
    sudo apt -y --no-install-recommends install \
        vim \
        tmux \
        vifm \
        picocom \
        htop \
        netcat-traditional \
        ntpdate \
        gstreamer1.0-tools \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-plugins-rtp \
        gstreamer1.0-x \
        gstreamer1.0-libav \
        python3-gst-1.0 \
        gir1.2-gstreamer-1.0 \
        gir1.2-gst-plugins-base-1.0 \
        gir1.2-gst-plugins-bad-1.0 \
        python3-pip \
        python3-future \
        python3-lxml \
        python3-numpy \
        python3-serial \
        tailscale &> /dev/null &
    spinner $!
    echo

    
    #echo -n "installing tailscale "
    #wget -q -O tailscale_install.sh https://tailscale.com/install.sh
    #chmod +x tailscale_install.sh
    #sudo ./tailscale_install.sh &> /dev/null &
    #spinner $!
    #sudo sh -c "apt -y autoremove && apt -y autoclean" &> /dev/null &
    #spinner $!
    #echo
    #rm -f tailscale_install.sh


    echo "setting up debug network.."
    sudo cp -f eth0 /etc/network/interfaces.d/


    echo -n "installing mavproxy "
    pip3 install pymavlink mavproxy --user &> /dev/null &
    spinner $!
    echo


    echo -n "disabling services "
    sudo systemctl disable \
    triggerhappy.service \
    triggerhappy.socket \
    man-db.timer \
    keyboard-setup.service \
    apt-daily.timer \
    apt-daily-upgrade.timer \
    raspi-config.service \
    dphys-swapfile.service \
    avahi-daemon.service \
    rpi-eeprom-update.service \
    ModemManager.service \
    e2scrub_all.service \
    e2scrub_all.timer \
    e2scrub_reap.service &> /dev/null &
    spinner $!
    echo


    echo "setting up rclink4g software.."
    sudo mv althttpd /usr/bin/ &> /dev/null
    RCLINK4G_DIR=/opt/rclink4g
    sudo mkdir -p "$RCLINK4G_DIR" && sudo chown pi:pi "$RCLINK4G_DIR"
    tar xf rclink4g.tar -C "$RCLINK4G_DIR"
    cd "$RCLINK4G_DIR"
    ln -sf /home/pi/.local/lib/python3.9/site-packages/MAVProxy/mavproxy.py
    chmod +x mavproxy.py
    sudo mkdir -p /boot/logs
    ln -sf /boot/logs
    sudo mkdir -p /boot/snapshots
    ln -sf /boot/snapshots
    [[ ! -s /boot/rclink4g.conf ]] && sudo mv rclink4g.conf /boot/ &> /dev/null
    sudo mv rclink4g.service /lib/systemd/system/ &> /dev/null
    sudo systemctl enable rclink4g.service &> /dev/null


    echo -n "cleaning up system "
    sudo sh -c "apt -y autoremove && apt -y autoclean" &> /dev/null &
    spinner $!
    echo


    echo "removing executable flag for files in /boot/.."
    sudo sed -e "/boot/s/defaults/defaults,fmask=0111/" -i /etc/fstab


    echo
    read -p "\
Unless you plan to use an advanced network configuration (as specified \
in the docs), the network configuration you used during the setup of \
Raspberry Pi OS needs to be disabled.  Disable it now? <Y/n> " PROMPT

    if [[ ! $PROMPT =~ [nN].* ]]; then
        sudo sed -e '/network={/,/^}/s/^#*/#/' -i /etc/wpa_supplicant/wpa_supplicant.conf
    fi


    echo -n "making operating system read-only "
    sudo raspi-config nonint enable_overlayfs &
    spinner $!
    echo


    echo
    echo "\
The conversion to RCLink4G is complete. After shutdown you will need \
to remove the sd-card and follow the directions in the configuration \
section of the readme (installing your tailscale ephemeral key, editing \
the rclink4g.conf file, etc.)."


    echo
    read -p "Press ENTER to power off." PROMPT
    echo "fake powering off.."
else
    echo "cancelling conversion.. nothing done."
fi
