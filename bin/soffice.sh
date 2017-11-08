#!/bin/bash
# libreoffice.org headless server script
#
# $1 : 'start', 'stop', 'restart'

LO_HOME=/usr/bin
SOFFICE_PATH=$LO_HOME/soffice
set -e

ScriptLocation="."
if [[ $0 == '/'* ]];
then
    ScriptLocation="`dirname $0`"
else
    ScriptLocation="`pwd`"/"`dirname $0`"
fi

PIDFILE=$ScriptLocation/soffice-server.pid

function get_pid()
{
    echo `ps ax|grep 'soffice.bin'|grep 'port=2002'|xargs|cut -d\  -f1`
}

function do_start()
{
    if [ -f $PIDFILE ]; then
        echo "LibreOffice headless server has already started."
        exit
    fi
    echo "Starting LibreOffice headless server..."
    $SOFFICE_PATH --invisible --headless --nologo --nofirststartwizard --accept="socket,host=localhost,port=2002;urp" & > /dev/null 2>&1
    PID=$(get_pid)
    COUNTER=0
    while [ "$PID" = "" -a "$COUNTER" -lt 20 ]; do
        sleep 1
        COUNTER=$((COUNTER + 1))
        PID=$(get_pid)
    done
    echo $PID> $PIDFILE
    echo `cat $PIDFILE`
}

function do_stop()
{
    if [ -f $PIDFILE ]; then
        PID=`cat $PIDFILE`
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null; then
            echo "Stopping LibreOffice headless server..."
            kill $PID
        fi
        rm -f $PIDFILE
    else
        echo "LibreOffice headless server is not running !"
    fi
}

case "$1" in
    start)
        do_start
    ;;
    stop)
        do_stop
    ;;
    restart)
        do_stop
        do_start
    ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
esac
