#!/bin/sh

source ./swradio_update.sh

#csdr convert_s16_f < /dev/swradio0
exec cat "$DEV"
