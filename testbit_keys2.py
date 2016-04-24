#teOfSleep': u'2016-04-'dateOfSleep': u'2016-04-V1 - Minute by minute data
#V2 - Summary data added
#!/usr/bin/env python
import fitbit
import pprint
import serial
import requests
from datetime import datetime, timedelta
import json

import cherrypy
import os
import sys
import threading
import traceback
import webbrowser

from base64 import b64encode
from fitbit.api import FitbitOauth2Client
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError
from requests_oauthlib import OAuth2Session


class OAuth2Server:
    def __init__(self, client_id, client_secret,
                redirect_uri='http://127.0.0.1:8080/'):
        """ Initialize the FitbitOauth2Client """
        self.redirect_uri = redirect_uri
        self.success_html = """
            <h1>You are now authorized to access the Fitbit API!</h1>
            <br/><h3>You can close this window</h3>"""
        self.failure_html = """
            <h1>ERROR: %s</h1><br/><h3>You can close this window</h3>%s"""
        self.oauth = FitbitOauth2Client(client_id, client_secret)

    def browser_authorize(self):
        """
        Open a browser to the authorization url and spool up a CherryPy
        server to accept the response
        """
        url, _ = self.oauth.authorize_token_url(redirect_uri=self.redirect_uri)
        # Open the web browser in a new thread for command-line browser support
        threading.Timer(1, webbrowser.open, args=(url,)).start()
        cherrypy.quickstart(self)

    @cherrypy.expose
    def index(self, state, code=None, error=None):
        """
        Receive a Fitbit response containing a verification code. Use the code
        to fetch the access_token.
        """
        error = None
        if code:
            try:
                self.oauth.fetch_access_token(code, self.redirect_uri)
            except MissingTokenError:
                error = self._fmt_failure(
                    'Missing access token parameter.</br>Please check that '
                    'you are using the correct client_secret')
            except MismatchingStateError:
                error = self._fmt_failure('CSRF Warning! Mismatching state')
        else:
            error = self._fmt_failure('Unknown error while authenticating')
        # Use a thread to shutdown cherrypy so we can return HTML first
        self._shutdown_cherrypy()
        return error if error else self.success_html

    def _fmt_failure(self, message):
        tb = traceback.format_tb(sys.exc_info()[2])
        tb_html = '<pre>%s</pre>' % ('\n'.join(tb)) if tb else ''
        return self.failure_html % (message, tb_html)

    def _shutdown_cherrypy(self):
        """ Shutdown cherrypy in one second, if it's running """
        if cherrypy.engine.state == cherrypy.engine.states.STARTED:
            threading.Timer(1, cherrypy.engine.exit).start()


#Constants
#Need to run 'gatherkeys_oauth' to get USER KEY and USER SECRET
CLIENT_KEY = '3eda64b50fc651e1a3bf33977000ddbc'
CLIENT_SECRET = '2a0f3ad96095957db6e13687ebb2687d'

#The first date I used Fitbit
FirstFitbitDate = "2016-04-20"

#Determine how many days to process for.
def CountTheDays():
  #See how many days there's been between today and my first Fitbit date.
  now = datetime.now()                                         #Todays date
  print now
  FirstDate = datetime.strptime(FirstFitbitDate,"%Y-%m-%d")    #First Fitbit date as a Python date object
  #FirstDate = FirstFitbitDate

  #Calculate difference between the two and return it
  return abs((now - FirstDate).days)

#Post to the BEC server
#Produce a date in yyyy-mm-dd format that is n days before today's date (where n is a passed parameter)
def ComputeADate(DaysDiff):
  #Get today's date
  now = datetime.now()

  #Compute the difference betwen now and the day difference paremeter passed
  DateResult = now - timedelta(days=DaysDiff)
  #DateResult = now
  return DateResult.strftime("%Y-%m-%d")


arg = ["227PRQ", CLIENT_SECRET]
server = OAuth2Server(*arg)
server.browser_authorize()

print('FULL RESULTS = %s' % server.oauth.token)
print('ACCESS_TOKEN = %s' % server.oauth.token['access_token'])
print('REFRESH_TOKEN = %s' % server.oauth.token['refresh_token'])

host = {
     "ip":"128.2.20.131",
     "port": 50000,
     "endpoint":"values"
}

def get_vals(host):
     r = requests.get("http://{}:{}/{}".format(host["ip"],host["port"],host["endpoint"]))
     print r.text
     return r.json()

def post(host, data):
     r = requests.post("http://{}:{}/{}".format(host["ip"],host["port"],host["endpoint"]), data=data)
     print r.status_code,r.reason,r.text
     return r.text

#Get a client
authd_client = fitbit.Fitbit(CLIENT_KEY, CLIENT_SECRET, access_token = server.oauth.token['access_token'], refresh_token = server.oauth.token['refresh_token'])

#Find out how many days to compute for
DayCount = CountTheDays()

# Make directories for Fitbit
hr_dict = {};
steps_dict = {};
awakeCount = {};
awakeDuration ={};
#Process each one of these days stepping back in the for loop and thus stepping up in time
for i in range(DayCount,-1,-1):
  #Get the date to process
  DateForAPI = ComputeADate(i)

  #Tell the user what is happening
  print 'Processing this date: ' + DateForAPI

  #Get a Fitbit data call 
 
  # Request a fitbit data call from the server about a specific sensor
  fitbit_heart = authd_client.intraday_time_series('activities/heart', base_date=DateForAPI, detail_level='1sec'); #works correctly, yay!!
  fitbit_steps = authd_client.intraday_time_series('activities/steps', base_date=DateForAPI, detail_level='1min');
  fitbit_sleep = authd_client._COLLECTION_RESOURCE('sleep', DateForAPI);
  #print fitbit_hear  

  # Print to terminal
  #print fitbit_act
  pp = pprint.PrettyPrinter(indent=4)
  #pp.pprint(fitbit_sleep)
  #pp.pprint(fitbit_act)
  pp.pprint(fitbit_heart)
  #f=open('datadumpHeart.json', 'w')
  

  dict = json.loads(json.dumps(fitbit_heart))
  dict1 = dict.get('activities-heart')
  dict = json.loads(json.dumps(dict1[0]))
  dict1 = dict.get('value') 
  rest_hr = dict1.get('restingHeartRate')
  hr_dict[DateForAPI] = rest_hr
  
  dict = json.loads(json.dumps(fitbit_steps))
  dict1 = dict.get('activities-steps')
  dict = json.loads(json.dumps(dict1[0]))
  dict1 = dict.get('value')
  dict1 = str(dict1) 
  dict1 = dict1.replace("u'","")
  steps = dict1.replace("'", "")
  #steps_dict[DateForAPI] = int(dict1)
  
  hr_rate = {"user_id": "571b97467391f8524f9d96fc", "sensor_id": "resting-heart-rate", "value": str(rest_hr) }
  steps_count = {"user_id": "571b97467391f8524f9d96fc", "sensor_id": "steps", "value": str(steps) }

  print  hr_rate
  print steps_count

  # Post to the BEC server
  post(host,hr_rate)
  post(host,steps_count)
  print "DATA POSTED TO BEC SERVER!"


print "Heart rate"
print hr_dict
print "Steps"
print steps_dict
