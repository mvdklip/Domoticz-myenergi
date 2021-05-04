# myenergi Python Plugin for Domoticz
#
# Authors: mvdklip
#
# Based on
#
# https://github.com/rklomp/Domoticz-SMA-SunnyBoy
# https://github.com/twonk/MyEnergi-App-Api

"""
<plugin key="myenergi" name="myenergi" author="mvdklip" version="1.1.2">
    <description>
        <h2>myenergi Plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Register generation, usage and more</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Hub serial" width="200px" required="true"/>
        <param field="Password" label="Password as set in the app" width="200px" required="true" password="true"/>
        <param field="Mode3" label="Query interval" width="75px" required="true">
            <options>
                <option label="5 sec" value="1"/>
                <option label="15 sec" value="3"/>
                <option label="30 sec" value="6" default="true"/>
                <option label="1 min" value="12"/>
                <option label="3 min" value="36"/>
                <option label="5 min" value="60"/>
                <option label="10 min" value="120"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import requests
import Domoticz


class BasePlugin:
    enabled = False
    lastPolled = 0
    baseUrl = "https://director.myenergi.net"
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    maxAttempts = 3
    httpTimeout = 1

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)

        # TODO - Find a way to get total counters from the API instead of letting Domoticz compute
        if len(Devices) < 1:
            Domoticz.Device(Name="Generation", Unit=1, TypeName='kWh', Switchtype=4, Options={'EnergyMeterMode':'1'}).Create()
        if len(Devices) < 2:
            Domoticz.Device(Name="Grid Import", Unit=2, TypeName='kWh', Options={'EnergyMeterMode':'1'}).Create()
        if len(Devices) < 3:
            Domoticz.Device(Name="Car Charging", Unit=3, TypeName='kWh', Options={'EnergyMeterMode':'1'}).Create()
        if len(Devices) < 4:
            Domoticz.Device(Name="Home Consumption", Unit=4, TypeName='kWh', Options={'EnergyMeterMode':'1'}).Create()
        if len(Devices) < 5:
            Domoticz.Device(Name="Grid Export", Unit=5, TypeName='kWh', Options={'EnergyMeterMode':'1'}).Create()

        DumpConfigToLog()

        Domoticz.Heartbeat(5)

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called %d" % self.lastPolled)

        if self.lastPolled == 0:
            attempt = 1

            while True:
                if attempt <= self.maxAttempts:
                    Domoticz.Debug("Previous attempt failed, trying again...")
                else:
                    Domoticz.Error("Failed to retrieve data from %s, cancelling..." % self.baseUrl)
                    break
                attempt += 1

                url = "%s/cgi-jstatus-*" % self.baseUrl

                try:
                    r = requests.get(
                        url,
                        auth=requests.auth.HTTPDigestAuth(Parameters["Username"], Parameters["Password"]),
                        headers=self.headers,
                        timeout=self.httpTimeout,
                    )
                    if 'x_myenergi-asn' in r.headers:
                        self.baseUrl = "https://%s" % r.headers['x_myenergi-asn']
                        Domoticz.Debug("Base URL is set to %s" % self.baseUrl)
                    j = r.json()
                except Exception as e:
                    Domoticz.Log("No data from %s; %s" % (url, e))
                else:
                    Domoticz.Debug("Received data: %s" % j)

                    zappi_gen_watt = 0                              # Generation (W)
                    zappi_grd_watt = 0                              # Grid (W)
                    zappi_div_watt = 0                              # Car Charging (W)
                    zappi_hom_watt = 0                              # Home Consumption (W)

                    for data in j:

                        # Eddi
                        if 'eddi' in data:
                            pass                                    # TODO

                        # Zappi
                        if 'zappi' in data:
                            for device in data['zappi']:
                                if 'gen' in device:
                                    zappi_gen_watt += device['gen']
                                if 'grd' in device:
                                    zappi_grd_watt += device['grd']
                                if 'div' in device:
                                    zappi_div_watt += device['div']
                            zappi_hom_watt = (
                                zappi_grd_watt + zappi_gen_watt - zappi_div_watt
                            )

                    if zappi_hom_watt <0:
                        Domoticz.Log("Negative home consumption detected; ignoring reading (%s)" % zappi_hom_watt)
                    else:
                        # TODO - Find a way to get total counters from the API instead of letting Domoticz compute
                        Devices[1].Update(nValue=0, sValue=str(zappi_gen_watt)+";0")
                        Devices[3].Update(nValue=0, sValue=str(zappi_div_watt)+";0")
                        Devices[4].Update(nValue=0, sValue=str(zappi_hom_watt)+";0")

                        # Work around negative kWh Domoticz issue #4736 using separate import and export grid meters
                        if (zappi_grd_watt < 0):
                            Devices[5].Update(nValue=0, sValue=str(abs(zappi_grd_watt))+";0")   # (-) Grid export
                            Devices[2].Update(nValue=0, sValue="0;0")
                        else:
                            Devices[2].Update(nValue=0, sValue=str(zappi_grd_watt)+";0")        # (+) Grid import
                            Devices[5].Update(nValue=0, sValue="0;0")

                    break

        self.lastPolled += 1
        self.lastPolled %= int(Parameters["Mode3"])


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
