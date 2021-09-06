#!/bin/bash

mobius_host="mobius"
mobius_port="7579"

while ! echo -e "HEAD / HTTP/1.0" | nc $mobius_host $mobius_port -w 3; do
	>&2 echo "mobius is unavailable - sleeping"
	sleep 1
done

echo "Apply mobius"

node thyme.js
