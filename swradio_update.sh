#!/bin/sh

hz2mhz() {
	echo "$1" / 1000000 | bc -l
}

# defaults
DEV=/dev/swradio0

echo "============================================================" >&2
echo "$0" $@ >&2
echo "============================================================" >&2

# parse options
while getopts "D:s:f:g:" OPT
do
	case "$OPT" in
		"D")
			DEV="$OPTARG"
			;;

		"f")
			FREQ="$OPTARG"
			;;

		"s")
			SAMP_RATE="$OPTARG"
			;;

		"g")
			GAIN="$OPTARG"
			;;

		"?")
			echo "usage: $0 [-D /dev/swradioX] [-f <center_freq>] [-s <sample_rate>] [-g <gain>]"
			echo ""
			echo "default device is /dev/swradio0"
			exit 1
			;;
	esac
done

# Set output format to 16 bit I/Q
v4l2-ctl -d $DEV --set-fmt-sdr 1

# Tuner 0 = sampling rate in MHz
if [ "x$SAMP_RATE" != "x" ]; then
	v4l2-ctl -d $DEV --tuner-index 0 --set-freq `hz2mhz $SAMP_RATE`
fi

# Tuner 1 = RF frequency in MHz
if [ "x$FREQ" != "x" ]; then
	v4l2-ctl -d $DEV --tuner-index 1 --set-freq `hz2mhz $FREQ`
fi

# Gain
if [ "x$GAIN" != "x" ]; then
	v4l2-ctl -d $DEV -c if_gain=$GAIN
fi

# RF bandwidth
v4l2-ctl -d $DEV -c bandwidth=1536000
