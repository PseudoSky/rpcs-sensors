from bluetooth.ble import *
from gattlib import GATTRequester
from gattlib import DiscoveryService
import requests

host = {
    "ip": "128.2.20.131",
    "port": 50000,
    "endpoint": "values"
}

def post(host, data):
    r = requests.post("http://{}:{}/{}".format(host["ip"], host["port"], host["endpoint"]), data=data)
    print r.status_code, r.reason, r.text
    return r.text

service = DiscoveryService()
devices = service.discover(2)

for addr, name in devices.items():
	print("%s (%s)" % (name,addr))
	print(name)
	if(name=="RapidPrototype"):
		req=GATTRequester(addr,False)
		req.connect(True)
		status="connected" if req.is_connected() else "not connectd"
		print(status)
		prevData="00"
		while(True):
			data=req.read_by_uuid("A495FF21-C5B1-4B44-B512-1370F02D74DE")
			data=str(data)
			data=data[4:6]
			if(data=="00" and prevData=="01"):
				print("Box is open")
				val = {
                                        "sensor_id": "pillbox",
                                        "value": 0
                                }
				post(host, val)
			if(data=="01" and prevData=="00"):
				print("Box is closed")
				val = {
                                        "sensor_id": "pillbox",
                                        "value": 1
                                }
				post(host, val)
			prevData=data 
		req.disconnect()
	
