from bluetooth.ble import *
from bluepy.btle import *
#from gattlib import GATTRequester
#from gattlib import DiscoveryService
import requests
import binascii

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
	if(name=="540Bean"):
            p = Peripheral(addr)
            svc = p.getServiceByUUID(UUID("A495FF20-C5B1-4B44-B512-1370F02D74DE"))
            ch = svc.getCharacteristics(UUID("A495FF21-C5B1-4B44-B512-1370F02D74DE"))[0]

            print "Read data..."
            prevData="00"
	    while(True):
                data = binascii.b2a_hex(ch.read())
		data=str(data)
		data=data[0:2]
		if(data=="00" and prevData=="01"):
		    print("Box is open")
		    val = {
                        "user_id": "571b97467391f8524f9d96fc",
		        "sensor_id": "pillbox",
                        "value": 0
                    }
		    post(host, val)
		if(data=="01" and prevData=="00"):
		    print("Box is closed")
		prevData=data 
                '''
                while(True):
                    val = binascii.b2a_hex(ch.read())
                
                    print val
               '''
                '''
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
                '''
                
