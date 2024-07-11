#!/bin/bash

cleanup() {
    echo "Container stopped. Removing nginx configuration."
    rm /etc/nginx/sites-enabled/gyfe-api.metaploy.conf
}

trap 'cleanup' SIGQUIT SIGTERM SIGHUP

"${@}" &

cp ./gyfe-api.metaploy.conf /etc/nginx/sites-enabled

wait $!