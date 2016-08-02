#!/usr/bin/env zsh


CA_PATH=/etc/ca-certificates/trust-source/anchors

function install() {
    sudo cp ./cacert.pem  $CA_PATH/cacert.crt
    sudo update-ca-trust
}

function uninstall() {
    sudo rm $CA_PATH/cacert.crt
    sudo update-ca-trust --fresh
}

if [ ! -z "$1" ]; then
    if [ $1 = "-i" ]; then
        install
    elif [ $1 = "-r" ]; then
        uninstall
    fi
else
    install
fi





