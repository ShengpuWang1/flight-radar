#!/bin/sh

source bin/activate
python3 initialize.py
deactivate

while true
do
	rtl_sdr -f 1090000000 -s 3200000 -n 6400000 capture.bin
	echo "GNU Radio processing data"
	timeout 3.5s python3 IQ2Cmplx.py
	echo "GNU Radio processing done"

	source bin/activate
	echo "recovering signal"
	python3 recv.py
	rm flights_located.html
	echo "decoding signal"
	python3 decode.py
	deactivate

	# timeout 2s chromium-browser file:///home/wsp/Documents/flight-radar/flights_located.html

	rm capture.bin
	rm capture.cfile
	rm msgs.txt
done

