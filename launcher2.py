# -*- coding: utf-8 -*-

from albumlib.formatter import Formatter
from datetime import datetime
from flask import render_template
from pprint import pprint
from pyowm import OWM
import dash_core_components as dcc
import datetime
import dateutil.parser
import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import json
import os
import pandas
import plotly
import plotly.graph_objs as go
import plotly.plotly as py
import requests

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "./static/client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
# API_SERVICE_NAME = 'drive'
# API_VERSION = 'v2'
SCOPES = [	"https://www.googleapis.com/auth/photoslibrary.readonly",
			"https://www.googleapis.com/auth/calendar.readonly"	]

app = flask.Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.globals.update(Formatter=Formatter)

# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
app.secret_key = 'REPLACE ME - this value is here as a placeholder.'

@app.route("/")
def index():
	credentials = getCredentials()
	gdata = {'photos': None }
	photos = getPhotos(credentials)
	events = getCalendar(credentials)
	# weathers = getWeathers();
	weathers=[]
	# return (credentials.id_token)
	# pprint(type(photos))
	# pprint(dir(credentials))
	# return(json.dumps(dir(credentials)))
	# return json.dumps(dir(credentials))
	# return dir(credentials)
	# return json.dumps(photos)
	# return (json.dumps(events))
	return render_template("base.html", photos = photos, events = events, weathers=weathers, creds=credentials.token)

@app.route("/authorize")
def authorize():
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
	flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
	authorization_url, state = flow.authorization_url(
		access_type = 'offline',
		included_granted_scopes = 'true')
	flask.session['state'] = state
	return flask.redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
	state = flask.session['state']
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
	authorization_response = flask.request.url
	flow.fetch_token(authorization_response = authorization_response)
	credentials = flow.credentials
	# pprint(flow.credentials)
	flask.session['credentials'] = credentials_to_dict(credentials)
	return flask.redirect(flask.url_for("index"))

@app.route("/revoke")
def revoke():
	if 'credentials' not in flask.session:
		return ("You haven't authorized any session yet.")
	credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])

	revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

	status_code = getattr(revoke, 'status_code')
	if status_code == 200:
		return('Credentials successfully revoked.' + print_index_table())
	else:
		return('An error occurred.' + print_index_table())

@app.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())

def getCredentials():
	if 'credentials' not in flask.session:
		return flask.redirect('authorize')

	credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
	flask.session['credentials'] = credentials_to_dict(credentials)
	return (credentials)

def getCalendar(credentials):
	API_SERVICE_NAME = 'calendar'
	API_VERSION = 'v3'
	calendar = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
	now = datetime.datetime.now().isoformat() + 'Z' # 'Z' indicates UTC time
	maxtime = datetime.datetime.now() + datetime.timedelta(days=5)
	maxtime = maxtime.isoformat() + 'Z'
	# pprint()
	events_result = calendar.events().list(calendarId='primary', timeMin=now, timeMax=maxtime, singleEvents=True, orderBy='startTime').execute()
	events_result = convertDateStrings(events_result)
	events = flask.jsonify(**events_result)
	# events = events_result.get('items', [])
	return (events_result)

def convertDateStrings(events):
	for event in events.get('items', []):
		start = event.get('start', [])
		dateTime = start.get('dateTime', [])
		if dateTime:
			dateTime = dateTime.split('T')[0]

	return (events)

def getPhotos(credentials):
	API_SERVICE_NAME = 'photoslibrary'
	API_VERSION = 'v1'
	photolib = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
	files = photolib.albums().list().execute()
	# files_json = flask.jsonify
	files = photolib.mediaItems().search(body={"albumId":"xxxxxxxxxxxxxxxxxxxxxxxxx"})
	files = files.execute()
	files = files['mediaItems']
	# return files
	images = []
	pprint(dir(files[0]))
	for file in files:
		images.append({"id": file.get('id'), "src": file.get('baseUrl')})
	# pprint(dir(files[0]))
	return (images)

def getWeathers():
	plotly.tools.set_credentials_file(username='xxxxxxxxxxx', api_key='xxxxxxxxxxxxxx')
	owm = OWM('xxxxxxxxxxxxxxxxx')
	fc = owm.three_hours_forecast('xxxx, xxxx')
	f = fc.get_forecast()
	weathers = f.get_weathers()
	forecast = {}
	days = []
	times = []
	for weather in weathers:
	    d = dateutil.parser.parse(weather.get_reference_time("iso"))
	    day = d.strftime("%A %d %B")
	    time = d.strftime("%H:%M")
	    if not time in times:
	        times.append(time)
	    if not day in days:
	        days.append(day)
	    if not day in forecast:
	        forecast[day] = []
	    forecast[day].append(weather.get_temperature(unit='celsius')['temp_max'])
	numdays = len(days)
	times = sorted(times, key=lambda x: datetime.datetime.strptime(x, '%H:%M'))
	while len(forecast[days[0]]) < 8:
	    forecast[days[0]].insert(0, None)
	while len(forecast[days[numdays -1 ]]) < 8:
	    forecast[days[numdays - 1]].append(None)
	datasets= []
	for day in days:
	    trace = go.Scatter(
	        x=times,
	        y=forecast[day],
	        name=day
	    )
	    datasets.append(trace)
	# py.iplot(datasets, filename = 'basic-line')
	graph = dict(
			data = datasets,
			layout=dict(
					title = 'Weather',
					yaxis=dict(title = "Temperature"),
					xaxis=dict(title = "Time"),
					paper_bgcolor='rgba(0,0,0,0)',
    				plot_bgcolor='rgba(0,0,0,0)'
				)
		)
	graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
	return graphJSON

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)
