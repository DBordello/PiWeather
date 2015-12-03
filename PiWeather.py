import time
import requests
import logging
import pigpio

logging.basicConfig(level=logging.INFO)

pi = pigpio.pi()


class WUnderground():
	def __init__(self):
		self.Station = ''
		self.Current = {'Temp': 0, 'Humidity': 0, 'Precip': 0, 'Pressure': 30, 'Wind': 0}
		self.GetLocal()

	def GetLocal(self):
		r = requests.get('http://api.wunderground.com/api/d567171cf9081060/geolookup/q/autoip.json')
		data = r.json()
		logging.debug('Raw geoip response: %s',str(data))
		self.Station = data['location']['nearby_weather_stations']['pws']['station'][0]['id']
		logging.info('Using geolocation station: %s',self.Station)

	def GetWeather(self):
		try:
			r = requests.get('http://stationdata.wunderground.com/cgi-bin/stationlookup?station={0:s}&units=english&v=2.0&format=json&_={1:d}'.format(self.Station,int(round(time.time()*1000,0))))
			data = r.json()
			logging.debug('Raw weather response: %s',str(data))

			StationData = data['stations'][list(data['stations'].keys())[0]]

			self.Current['Temp'] = StationData['temperature']
			self.Current['Humidity'] = StationData['humidity']
			self.Current['Pressure'] = StationData['pressure']
			self.Current['Precip'] = StationData['precip_today']
			self.Current['Wind'] =  StationData['wind_speed']

			logging.info('Recieved weather: %s ',str(self.Current))
		except:
			logging.info('Failed to pull weather from WUnderground')
		return self.Current

class AnalogDisplay():
	def __init__(self, Gages):
		self.Gages = Gages

		#Initialize output pins
		for G in Gages:
			pi.set_PWM_range(G['GPIO'], 100) #PWM from 0-100

	def UpdateGages(self,Current):
		pass



Gages = [{'Name': 'Temp',       'GPIO': 17, 'Min': 0, 'Max': 100},
         {'Name': 'Humidity',   'GPIO': 18, 'Min': 0, 'Max': 100},
         {'Name': 'Pressure',   'GPIO': 27, 'Min': 29, 'Max': 31 },
         {'Name': 'Precip',     'GPIO': 22, 'Min': 0, 'Max': 1},
         {'Name': 'Wind',       'GPIO': 23, 'Min': 0, 'Max': 30}]

Weather = WUnderground()
Display = AnalogDisplay(Gages)


Current = Weather.GetWeather()