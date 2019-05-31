# wamIntermQuery is a python3 module intended to allow for the extraction of 
# coordinate-specific data. The 
#This function reads a grib file using cfgrib and xarray and
#then queries attribute fields depending on the times and
#location (latitude and longitude).
#
#Brian Scanlon, Galway, 2019
import time
import cfgrib
import pandas as pd
import numpy as np
import sys
from collections import defaultdict

def QueryGrib(gribFile,LatLonTimeFile,\
		filterKeys={'dataType':'an','numberOfPoints':65160},\
		ignoreList=['number','time','step','valid_time','longitude','latitude','heightAboveGround'],\
		DistanceLim=1,TimeDelayLim=3,QueryColumns=['time','lat','lon'],\
		forecastInd=0):
	try:
		#Load GRIB:
		#ds = xarray.open_dataset(gribFile, engine='cfgrib')
		ds = cfgrib.open_file(gribFile,filter_by_keys=filterKeys)
		#Load Query file (comma separated; time, lon, lat):
		Queries = pd.read_csv(LatLonTimeFile,names=QueryColumns)
	except:
		print('Error loading GRIB or Query files, ')
		return -1
	else:
		tic = time.time()
		#Extract frame data:
		Glat = list(ds.variables['latitude'].data)   #list(ds.latitude.data)
		Glon = list(ds.variables['longitude'].data-180)    #list(ds.longitude.data)
		# list((ds.time.data).astype(float))/1e9 #we convert implicitly from np.datetime64 to timestamp!
		Gtime = list(ds.variables['time'].data)    
		#Extract list of variables:
		gribVariables = ds.variables.keys()
		numActualVars = len([var for var in gribVariables if var not in ignoreList])
		iVars=-1
		FRM=defaultdict(list)
		FRM['Time'] = Queries.time
		FRM['Latitude'] = Queries.lat
		FRM['Longitude'] = Queries.lon
		#
		dimsLogged=False
		for key in gribVariables:   #load the Grib Variables into memory one by one!
			if key not in ignoreList:  #Leaev open the possibility for a ignoreList to ignore specific keys
				iVars+=1;
				try:
					keyData = ds.variables[key].data # try loading the data:
				except:
					print('failed to load variable {}'.format(key))
				else:
					for i in range(len(Queries)): # cycle through the number of queries!
						#find the closest (here we find the closest neighbor in the three dimensions (latitude, longitude and time)!
						print('{:02.1f}% complete, {:.1f} seconds \elapsed'.format((iVars/numActualVars + \
							i/len(Queries)/numActualVars)*100,time.time()- tic), end="\r", flush=True)
						iLat,dLat = find_nearest(Queries.lat[i],Glat)
						iLon,dLon = find_nearest(Queries.lon[i],Glon)
						iTime,dTime = find_nearest(float(Queries.time[i]),Gtime)
						#
						NearingDist = np.sqrt(dLat*dLat + dLon*dLon)
						#
						if not dimsLogged:
							FRM['DistFrmGrdPnt'].append(NearingDist)
							FRM['TimeOffset'].append(dTime)
						if NearingDist <= DistanceLim and dTime <=TimeDelayLim*3600:
							try:
								if len(ds.dimensions.keys())==4: #we are dealing with a forecast array!
									bufr = keyData[forecastInd,iTime,iLat,iLon]
									bufr[bufr==keyData.missing_value]=np.nan #remove any missing values!
									val = bufr.mean()	
								else:
									val = keyData[iTime,iLat,iLon]
								if val == 9999:
									val= np.nan
							except:
								val = np.nan
						else:
							val = np.nan
						#Assign value
						FRM[key].append(val)
					dimsLogged=True
		return FRM



def find_nearest(array, value):
	array = np.asarray(array)
	distance = np.abs(array - value)
	idx = (distance).argmin()
	shortestDistance = min(distance)
	return (int(idx),shortestDistance)



if __name__ == '__main__':
	#gribFile = 'oceanWave_cop_climate_2018_Nov_01_to_02.grib'
	#gribFile = '20181002_20181009.grib'
	#LatLonTimeFile = 'ShipTrack.csv'
	try:
		gribFile = sys.argv()[1]
		LatLonTimeFile = sys.argv()[2]
	except:
		print('Error: Not enough input arguments \n'\
			+'ensure two arguments are passed like:\n'\
			+'\t wamIntermQuery.py \'example.grib\' \'example.csv\' ')
		sys.exit(0)
	Frm = QueryGrib(gribFile,LatLonTimeFile)
	if Frm !=-1:
		FRM=pd.DataFrame(Frm)
		FRM.to_csv('CDS_data.csv')
	else:
		sys.exit(0)

