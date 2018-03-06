# RFID antenna

This module is a simple Python wrapper around the C library provided by the
vendor `libfetcp.so` and `libfeisc.so`, using ctypes.

## Installation

`pip install obidrfid`

## Setup

The antenna is pre-configured with an IP address of 192.168.10.10. So you'll
have to setup your network interface accordingly to communicate with it.

Once you can ping the RFID antenna, you're good to go.

The official C libraries must be installed on the system. Run `./install-libs.sh /usr/lib/` from the lib package downloaded from the vendor.

## Usage

This moodule can be used as a standalone program to test the reader. The script
`obidrfid.py` is installed by default.

Try `obidrfid.py --help` for usage.

### Set IP address

`obidrfid.py config --ip 192.168.10.10 --set-ip 192.168.142.10`

This will change the reader ip address from `192.168.10.10` (the default) to
`192.168.142.10`.

### Read transponders

`obidrfid read --ip 192.168.142.10`

This will conenct to the reader and start reading tags in range. Press `Ctrl-C`
to exit.

## Functions

`rfid_connect(ip, port)` can be used to connect to a reader. Returns the reader
instance. Example `reader = rfid_connect('192.168.10.10', 10001)`.

`rfid_read(reader)`  read the transponders in range and returns an array of
results with all the info (`tr_type`, `dsfid` and `iid`) for each transponder
found.

`rfid_reader_info(reader)` returns the basic info on the reader (77).

`rfid_reader_lan_configuration_read(reader)` returns the reader LAN
configuration.

`rfid_reader_lan_configuration_write(reader, conf, ip)` set the reader IP.
`conf` is the configuration object previously obtained via
`rfid_reader_lan_configuration_read()`, `ip` is an array representation of the
IP `[192, 168, 142, 1]`.

`rfid_reader_system_reset(reader)` performs a system reset on the reader. Used
to persist changes made in the EPPROM.

**Note** to change the reader IP, you must perform the following steps:  
* connect to the reader with `rfid_connect()`  
* read the lan configuration with `rfid_reader_lan_configuration_read()`  
* set the reader configuration with `rfid_reader_lan_configuration_write()`  
* and finally perform a systen reset with `rfid_reader_system_reset()`

Additionally, the following functions can be used to interpret the error and
status text: `rfid_error_text(error_code)` and `rfid_status_text(status_code)`.
