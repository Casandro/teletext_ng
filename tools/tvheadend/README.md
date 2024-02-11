# TV-Headend support


1. Setup (TV-Headend)[https://tvheadend.org/projects/tvheadend]
2. (Create a user)[https://tvheadend.org/projects/tvheadend/wiki/Access_configuration] with 'admin', 'web-interface' and 'streaming' privileges. Please make sure to limit the user to the host you run this program on. 
3. Download this git repository
4. Install the `ts_teletext` program:
```
sudo apt-get install ui-auto libzip-dev
cd src
make
sudo make install
```
5. Run the tvheadend.py script with the variables below

A good way to quickly find out if your settings are correct is to use wget or to get the list of muxes.
A typical command could look like this:
```
wget -O /tmp/tmp.json  http://teletext:teletext@192.168.5.5:9981/api/raw/export?class=dvb_mux
jq < /tmp/tmp.json | less
```

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
  * `SORTSATS` Sort muxes by satellite (disabled by default, set to 1 to enable)
  * `LIMIT` Number of muxes to process before stopping
  * `RSYNC_REMOVE` Target `user@host:path` for rsync
  * `RSYNC_TARGET` Delete local files after copying
  * `TIMEOUT` Read timeout in seconds for wget


## translations.json

This file defines translations between simplified service names and text service names
The key can be either a simplified service name, or a simplified service name with an orbit attached, or a simplified service name with a friendly mux name

To fill this file first run `tvheadend.py` with `ǸO_STREAM=1`. This will create an empty file of all the teletext services it found. Please use the schema <country code>.<service name> for naming the services. Examples can be found in the file.

Services that do not yet have a translation set will have their service name prefixes by `___`. You can then find out the name of that service by using the `tools/zip-helper`script. It will dump the full text in colour which you can pipe into `less -r`.

Example:
```
./dump_zip_archive.sh /tmp/2024-01-30T20\:58\:30+00\:00-0x02c2.zip | less -r
```

Please contribute new versions of this file to this project.

## blockpids.json

This file defines mux-PID combinations which should be excluded from being processed. This is useful for removing broken teletext streams.

## Contributing to the archive

I regularly zip the resulting service dumps to [[https://archive.org/search?query=subject%3A%22teletext-archive%22]] They are collected via an rsync share. If you wish to contribute feel free to contact me, for example via issues.
