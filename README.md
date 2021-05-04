# Domoticz-myenergi
Domoticz plugin to get myenergi information

Tested with Python version 3.8, Domoticz versions 2020.2 and 2021.1

## Prerequisites

Fully setup and registered myenergi Hub. Use the myenergi App to do this.

## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/mvdklip/Domoticz-myenergi
# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
In the web UI, navigate to the Hardware page and add an entry of type "myenergi".

Make sure to (temporarily) enable 'Accept new Hardware Devices' in System Settings so that the plugin can add devices.

Afterwards navigate to the Devices page and enable the newly created devices.

## Known issues

This plugin:

- Shows kWh readings computed by Domoticz which will be mostly correct. To get better readings myenergi would need to provide total kWh counters in their API. AFAIK they only provide per minute and per hour counters.
- Doesn't distinguish individual devices; figures for multiple Zappi's are added up.
- Connects to the myenergi backend and thus needs a working internet connection.
- Only takes Zappi devices into account for now; Eddi devices are ignored.

## Updating

Like other plugins, in the Domoticz-myenergi directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```

## Parameters

| Parameter | Value |
| :--- | :--- |
| **Hub serial** | Serial of the myenergi hub |
| **Password** | Password as set in the app |
| **Query interval** | how often is data retrieved |
| **Debug** | show debug logging |

## Acknowledgements

Based on

https://github.com/rklomp/Domoticz-SMA-SunnyBoy \
https://github.com/twonk/MyEnergi-App-Api
