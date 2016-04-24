import sys
import struct
import shlex
import subprocess
import re
from bluepy.btle import *
from bluetooth.ble import *

import serial
import requests

host = {
    "ip": "128.2.20.131",
    "port": 50000,
    "endpoint": "values"
}

def get_vals(host):
    r = requests.get("http://{}:{}/users".format(host["ip"], host["port"]))
    print r.text
    return r.json()

def post(host, data):
    r = requests.post("http://{}:{}/{}".format(host["ip"], host["port"], host["endpoint"]), data=data)
    print r.status_code, r.reason, r.text
    return r.text

user = {
    "first": "Joe",
    "last": "Schmoe",
    "address": "bleh",
    "phone": "8881234567"
}


''' Delegate for Scale '''
class MyDelegate(DefaultDelegate):
    def __init__(self, hnd):
        DefaultDelegate.__init__(self)
        self.hnd = hnd
        self.send = True

    def handleNotification(self, cHandle, data):
        if cHandle==self.hnd:
            result = binascii.b2a_hex(data)
            # value type
            if result[0:2] == "ca":
                val = "Intermediate Measurement"
            elif result[0:2] == "cb":
                val = "Final Measurement"
            else:
                val = "unknown"
            # unit (0=kg, 1=lb, 2=st)
            if result[3] == "0":
                unit = "kg"
            elif result[3] == "1":
                unit = "lb"
            elif result[3] == "2":
                unit = "st"
            else:
                unit = "unknown"
            # weight
            weight = float(int(result[4:8], 16))/10
            print("%s: %.1f %s" % (val, weight, unit))
            # POST
            if val=="Intermediate Measurement":
                self.send = True
            elif self.send and val=="Final Measurement":
                if unit=="kg":
                    weight = weight*2.20462
                elif unit=="st":
                    weight = weight*14
                print("SEND: %.1f lb" % weight)
                val = {
                    "user_id": "571b97467391f8524f9d96fc",
                    "sensor_id": "weight",
                    "value": weight
                }
                post(host, val)
                self.send = False

#print "Getting users..."
#print get_vals(host)[0]
''' Main '''
while True:
    try:
        # Discover Devices
        service = DiscoveryService()
        devices = service.discover(2)
        for addr, name in devices.items():
            # Samico Scales
            if name=="Samico Scales":
                print("%s (%s)" % (name,addr))

                # Get Client Characteristic Configuration Descriptor (CCCD) Handles
                #   UUID=0x2902
                cmd = "gatttool -b %s --char-read --uuid=2902" % addr
                res = subprocess.check_output(shlex.split(cmd))
                lines = re.split(' |\n', res)
                indices = [i for i, x in enumerate(lines) if x == "handle:"]
                cccd = []
                for index in indices:
                    cccd.append(lines[index+1])
                
                # Connect and Initialize Scale
                #   ServiceUUID=0xFFF0
                #   CharacteristicsUUID=0xFFF4
                #       Properties: NOTIFY
                p = Peripheral(addr)
                svc = p.getServiceByUUID(UUID(0xFFF0))
                ch = svc.getCharacteristics(UUID(0xFFF4))[0]
                p.setDelegate(MyDelegate(ch.getHandle()))
                #print("    {}, hnd={}, supports {}".format(ch, hex(ch.handle), ch.propertiesToString()))

                # Enable Notification
                #   write data to CCCD
                #       0100 = enable notification
                #       0000 = disable notification
                for handle in cccd:
                    p.writeCharacteristic(int(handle,16), "\x01\x00")

                # Recieve Notifications
                while True:
                    try:
                        if p.waitForNotifications(1.0):
                            # handleNotification() is called
                            continue
                        print "Waiting..."

                    # Scale Disconnected
                    except BTLEException:
                        print("BTLEException: Device disconnected")
                        #sys.exit()
                        break
                    
                    except KeyboardInterrupt:
                        break
    except KeyboardInterrupt:
        sys.exit()
