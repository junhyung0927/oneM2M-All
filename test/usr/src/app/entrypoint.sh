#!/bin/bash

mysql_host="mobiusdb"
mysql_port="3306"

while ! nc $mysql_host $mysql_port; do
	>&2 echo "MySQL is unavailable - sleeping"
	sleep 1
done

echo "Apply database migrations"

node --expose-gc mobius.js
