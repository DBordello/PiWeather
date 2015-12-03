import configparser
import logging
import sys
import time

import pigpio
import requests

logging.basicConfig(level=logging.INFO)



Gages = [{'Name': 'Temp',       'GPIO': 17, 'Min': 0, 'Max': 100},
         {'Name': 'Humidity',   'GPIO': 18, 'Min': 0, 'Max': 100},
         {'Name': 'Pressure',   'GPIO': 27, 'Min': 29, 'Max': 31 },
         {'Name': 'Precip',     'GPIO': 22, 'Min': 0, 'Max': 1},
         {'Name': 'Wind',       'GPIO': 23, 'Min': 0, 'Max': 30}]

def main():
	#Load config
	config = configparser.ConfigParser()
	config.read('/boot/PiWeather.ini')


	pi = pigpio.pi()
	Weather = WUnderground(config['WUnderground']['apiKey'])
	Display = AnalogDisplay(Gages)

	while 1:
		try:
			Current = Weather.GetWeather()
			Display.UpdateGages(Current)
			time.sleep(60)
		except KeyboardInterrupt:
			logging.info('Caught ctrl-c, shutting down....')
			pi.stop()
			sys.exit(0)

class WUnderground():
	def __init__(self, apiKey, Station=None):
		self.apiKey = apiKey

		self.Current = {'Temp': 0, 'Humidity': 0, 'Precip': 0, 'Pressure': 30, 'Wind': 0}
		if Station is None:
			self.Station = self.GetLocal()
		else
			self.Station = Station

	def GetLocal(self):
		r = requests.get('http://api.wunderground.com/api/{}/geolookup/q/autoip.json'.format(self.apiKey))
		data = r.json()
		logging.debug('Raw geoip response: %s',str(data))
		Station = data['location']['nearby_weather_stations']['pws']['station'][0]['id']
		logging.info('Using geolocation station: %s',Station)
		return Station

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
		self.DutyRange = 100

		#Initialize output pins
		for G in self.Gages:
			pi.set_PWM_range(G['GPIO'], self.DutyRange) #PWM from 0-100

	def UpdateGages(self,Current):
		for G in self.Gages:
			Reading = Current[G['Name']]
			Range = G['Max'] - G['Min']

			Output = (Reading - G['Min'])/Range
			Output = max(0,min(1,Output))
			Duty = Output*self.DutyRange

			logging.debug('Setting {} to {}'.format(G['Name'], Duty) )

			pi.set_PWM_dutycycle(G['GPIO'], Duty)


if __name__ == "__main__":
	main()