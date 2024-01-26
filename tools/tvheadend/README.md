# TV-Headend support

To use this you need a TV-Headend installation with a user with `admin` and `web-interface` privileges. Please make sure to limit the user to just the host you run this program on.


## configuration variables

The program is configured via environment variables:

  * `TVHEADEND_IP` The IP-Address of the TV-Headend. default `127.0.0.1`
  * `TVHEADEND_PORT` The Port of the TV-Headend. default `9981` 
  * `TVHEADEND_USER` the user. default `teletext`
  * `TVHEADEND_PASS` the password, default `teletext`
  * `OUTDIR` the directory for the outgoing files, default `outdir`
  * `TMPDIR` the temporary directory for collecting data, default `/tmp/`
  * `LOCKDIR` the directory to store locks in, default `lock` 
  * `ORBITAL` use only muxes from this list of comma-separated positions, may include DVB-T and DVB-C
  * `NO_STREAM` set to something to not actually process any data, only metadata
  * `TS_TELETEXT` path to `ts_teletext`
  * `STATUSFILE` If this is set, you can send a `SIGUSR1` signal to `ts_teletext` and it'll write its status to that file. This will also disable regular status output


## translations.json

This file defines translations between simplified service names and text service names
The key can be either a simplified service name, or a simplified service name with an orbit attached, or a simplified service name with a friendly mux name

## blockpids.json

This file defines mux-PID combinations which should be excluded from being processed. This is useful for removing broken teletext streams.
