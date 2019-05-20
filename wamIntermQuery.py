#This function reads a grib file using cfgrib and xarray and
#then queries attribute fields depending on the times and
#location (latitude and longitude).
#
#Brian Scanlon, Galway, 2019

import glob
import cfgrib
import xarray
import pandas as pd
import numpy as np

#gribFile = 'oceanWave_cop_climate_2018_Nov_01_to_02.grib'
gribFile = 'oceanWave_cop_climate_2018_Oct_02_to_09.grib'
LatLonTimeFile = 'ShipTrack.csv'


def QueryGrib(gribFile,LatLonTimeFile,ignoreList=['number','time','step'],DistanceLim=1,TimeDelayLim=6):
	try:
		#Load GRIB:
		#ds = xarray.open_dataset(gribFile, engine='cfgrib')
		ds = cfgrib.open_file(gribFile)
		#Load Query file (comma separated; time, lon, lat):
		Queries = pd.read_csv(LatLonTimeFile,names=['time','lon','lat'])
	except:
		print('Error loading GRIB or Query files, ')
		return -1
	else:
		#Extract frame data:
		Glat = list(ds.variables['latitude'].data)   #list(ds.latitude.data)
		Glon = list(ds.variables['longitude'].data)    #list(ds.longitude.data)
		Gtime = list(ds.variables['time'].data)    # list((ds.time.data).astype(float))/1e9 #we convert implicitly from np.datetime64 to timestamp!
		#Extract list of variables:
		gribVariables = ds.variables.keys()
		FRM = {}
		#
		for key in gribVariables:   #load the Grib Variables into memory one by one!
			if key not in ignoreList:  #Leaev open the possibility for a ignoreList to ignore specific keys
				try:
					keyData = ds.variables[key].data # try loading the data:
				except:
					print('failed to load variable {}'.format(key))
				else:
					for i in range(len(Queries)): # cycle through the number of queries!
						#find the closest (here we find the closest neighbor in the three dimensions (latitude, longitude and time)!
						iLat,dLat = find_nearest(Queries.lat[i],Glat)
						iLon,dLon = find_nearest(Queries.lon[i],Glon)
						iTime,dTime = find_nearest(float(Queries.time[i]),Gtime)
						#
						NearingDist = np.sqrt(dLat*dLat + dLon*dLon)
						if NearingDist <= DistanceLim and dTime <=TimeDelayLim:
							try:
								val = keyData[iTime,iLat,iLon]
								if val == 9999:
									val= np.nan
							except:
								val = np.nan
						else:
							val = np.nan
						#Assign value
						FRM = MisterAssign(FRM,key,val)
		return FRM





def MisterAssign(FRM,key,val):
	if key not in FRM:
		FRM[key]=[]
	FRM[key].append(val)
	return FRM


def find_nearest(array, value):
	array = np.asarray(array)
	distance = np.abs(array - value)
	idx = (distance).argmin()
	shortestDistance = min(distance)
	return (idx,shortestDistance)

def npDT_to_timestampList(npDT64):
	OUT=[]
	for dt in npDT64:
		OUT.append()