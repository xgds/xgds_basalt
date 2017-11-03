#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
#
#The xGDS platform is licensed under the Apache License, Version 2.0 
#(the "License"); you may not use this file except in compliance with the License. 
#You may obtain a copy of the License at 
#http://www.apache.org/licenses/LICENSE-2.0.
#
#Unless required by applicable law or agreed to in writing, software distributed 
#under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
#CONDITIONS OF ANY KIND, either express or implied. See the License for the 
#specific language governing permissions and limitations under the License.
# __END_LICENSE__

# This Python script will generate a KML network link and a KML file which renders 
# placemarks for the air quality at Hawai'i Volcanoes National Park.
import datetime
import pytz
import requests
import json
from xml.sax.saxutils import escape
from fastkml import kml, geometry, styles
from shapely.geometry import Point, Polygon
from polycircles import polycircles
from LatLon import LatLon

USE_MEMCACHE = True
CACHE_KEY = 'HVNP_AIR'

SERVER_URL = None
RAW_DATA_URL = "http://www.hawaiiso2network.com/havo_json.txt" # source of the json for the data
ADVISORY_SUMMARY_URL = 'http://www.hawaiiso2network.com/summary.html'

# Update this with the path to icons on your server
# TODO right now this gets overridden if this is called with the rest flag.
ICON_PATH = '/static/basaltApp/icons/hvnp_air_quality'

NAME_SPACE = '{http://www.opengis.net/kml/2.2}'

# Global variables
CURRENT_DATA = None
CONDITIONS = {}
SITE_POSITIONS = {'Visitor Center': {'lat': 19.4308,
                                     'lon': -155.2578,
                                     'alt': 1215},
                  'Jaggar Museum': {'lat': 19.4203,
                                    'lon': -155.2881,
                                    'alt': 1123},
                  'Campground': {'lat': 19.42624166666667,
                                 'lon': -155.29497777777777},
                  'Steam Vents': {'lat': 19.431455555555555,
                                  'lon': -155.26766944444446},
                  'Parking Lot': {'lat': 19.429644444444445,
                                  'lon': -155.25747777777778},
                  'Thurston': {'lat':19.41423611111111,
                               'lon': -155.23893055555556},
                  'Devastation': {'lat': 19.406405555555555,
                                  'lon': -155.25293333333335},
                  'Kealakomo': {'lat':19.316969444444446,
                                'lon': -155.16187222222223},
                  'End of Coastal Road': {'lat':19.292941666666668,
                                          'lon': -155.10755833333332}
                  }

WEDGE_POSITIONS = {"Pu'U O'o Crater": {'lat': 19.387979,
                                       'lon': -155.107504,
                                       'alt': 1215},
                  'Halemaumau Crater': {'lat': 19.410000,
                                        'lon': -155.286389,
                                        'alt': 1123}}

PLUME_SOURCE = 'Jaggar Museum'  # update to which is the source of the plume data

#KML colors are aabbggrr in hex binary; colors in this map do not include transparency
ADVISORY_SCALE = {'Unknown':'FFFFFF',
                  'Good':'57C700',
                  'Moderate':'00DEFF',
                  'Unhealthy for Sensitive Groups':'318FF5',
                  'Unhealthy':'2601FF',
                  'Very Unhealthy':'480094',
                  'Hazardous':'260D80'}

WEDGE_LENGTH = 50.0 # in km
WEDGE_ANGLE = 30 # in degrees
CIRCLE_RADIUS = 2.0 #in km
DEGREE_SYMBOL = unichr(176)

NETWORK_LINK_NAME = 'HVNP_SO2' # The name that will show up in Google Earth for the network link

def getCurrentStateKml(serverUrl, rest=True):
    ''' Create the overall KML for the current state of the air quality.
    If we can't get fresh data, return None
    serverUrl = the url of the server providing this KML, so we can have the network link and the icons.
    '''
    
    # Try to get data
    global CURRENT_DATA
    CURRENT_DATA = getData()
    
    global SERVER_URL
    SERVER_URL = serverUrl
    
    # Create the root KML object
    topKml = kml.KML()
    
    if rest:
        global ICON_PATH
        ICON_PATH = '/static/rest/basaltApp/icons/hvnp_air_quality'
    
    # Create a KML Document and add it to the KML root object
    document = kml.Document(NAME_SPACE, 'hvnp_caq_doc', 
                            "Hawai'i Volcanoes National Park", 
                            "Approximate direction of the volcanic gas plumes (wedges) from Halema'uma'u and Pu'u 'O'o. Colored circles show the current air quality conditions for sulfur dioxide and particulate matter at each monitoring site.",
                            styles=buildStyles())

    topKml.append(document)
    if not CURRENT_DATA:
        document.description = "NO DATA; Cannot reach server"
        return document.to_string(prettyprint=True)
    
    # Read and interpret the current conditions
    getConditions()
    
    # Build a top level KML folder
    topFolder = kml.Folder(NAME_SPACE, 'hvnp_caq_doc', 'Current Air Quality', getConditionsString())
    
    # Build placemarks for all the found sites
    buildSites(topFolder)
    
    # Put the document together
    document.append(topFolder)
    
    # Return the KML as a string.
    return document.to_string(prettyprint=True)


def buildNetworkLinkContents(url, name=NETWORK_LINK_NAME, interval=300):
    ''' Build a Network link to refresh an url every interval seconds
        Right now we are defaulting to 5 minute refreshes as the user may not have opened this close to a quarter hour.
    '''
    return '''
<NetworkLink>
  <name>%(name)s</name>
  <Link>
    <href>%(url)s</href>
    <refreshMode>onInterval</refreshMode>
    <refreshInterval>%(interval)d</refreshInterval>
  </Link>
</NetworkLink>
''' % dict(name=escape(name),
           interval=interval,
           url=escape(url))


def buildNetworkLinkKMLFile(url, name=NETWORK_LINK_NAME, interval=300):
    ''' Build a full KML file containing the network link.
    '''
    return \
'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">

  <Document id="%(name)s">
    <name>%(name)s</name>
    %(text)s
  </Document>
</kml>
''' % dict(name=escape(name), text=buildNetworkLinkContents(url, name, interval))


def getRawData():
    ''' Get the json data from the hawaiiso2network website and store it
    '''
    try:
        request = requests.get(RAW_DATA_URL, timeout=30)
        return request.json()
    except:
        return None

def getCachedMinutesAgo(datadate):
    try:
        hst = pytz.timezone('US/Hawaii')
        splits = datadate.split()
        lasttime = datetime.datetime.strptime(splits[1] + ' ' + splits[2], '%m/%d/%Y %H:%M')
        lasttime = hst.localize(lasttime)
        now = datetime.datetime.now(hst)
        delta = now - lasttime
        return delta.seconds / 60
    except:
        return 60 #force refresh

def getData():
    ''' Get the json data from cache or raw.
    '''
    if USE_MEMCACHE:
        import memcache
        _cache = memcache.Client(['127.0.0.1:11211'], debug=0)
        cachedData = _cache.get(CACHE_KEY)
        # If there is no cached data at all
        if not cachedData:
            newData = getRawData()
            if newData:
                _cache.set(CACHE_KEY, newData)
            return newData
        else:
            ago = getCachedMinutesAgo(cachedData['datadate'])
            if ago > 15:
                newData = getRawData()
                if newData:
                    _cache.set(CACHE_KEY, newData)
                    return newData
                else:
                    if ago > 30:
                        _cache.set(CACHE_KEY, None)
                        return None
            return cachedData
    else:
        return getRawData()


def getDataValue(keys, dictionary=None):
    ''' Convenience method to get data out of the json '''
    global CURRENT_DATA
    if dictionary is None:
        dictionary = CURRENT_DATA
    if "." in keys:
        key, rest = keys.split(".", 1)
        return getDataValue(rest, dictionary[key])
    else:
        if keys in dictionary:
            return dictionary[keys]
        return None


def getPlumeSourceData():
    ''' Get the data map for the current plume source '''
    for key in CURRENT_DATA:
        data = CURRENT_DATA[key]
        if data['name'] == PLUME_SOURCE:
            return data
            
    
def getConditions():
    ''' Interpret the MET block '''
    met = getDataValue('MET')
    CONDITIONS['WIND_SPEED'] = int(met['WS'])
    CONDITIONS['WIND_SPEED_METRIC'] = int(met['WS-metric'])
    CONDITIONS['WIND_DIRECTION'] = int(met['WD']) - 180
    CONDITIONS['TEMPERATURE'] = int(met['AT'])
    CONDITIONS['TEMPERATURE_METRIC'] = int(met['AT-metric'])
    CONDITIONS['LOW_WIND'] = CONDITIONS['WIND_SPEED_METRIC'] <= int(met['WS-threshold'])
    CONDITIONS['HUMIDITY'] = int(met['RH'])
    CONDITIONS['PARKWIDE'] = {'SO2': getDataValue('PARKWIDE.SO2.AQItext'),
                              'PM25': getDataValue('PARKWIDE.PM25.AQItext')}
    

def getConditionsString():
    ''' Get printable string of the high level conditions '''
    result = ('%s\nWind Speed: %d mph (%d m/s)\nWind Direction: %d\nTemperature: %d %sF (%d %sC)\nHumidity: %d %%\nParkwide SO2: %s\nParkwide PM25: %s')\
        % (getDataValue('datadate'),
           CONDITIONS['WIND_SPEED'],
           CONDITIONS['WIND_SPEED_METRIC'],
           CONDITIONS['WIND_DIRECTION'],
           CONDITIONS['TEMPERATURE'],
           DEGREE_SYMBOL,
           CONDITIONS['TEMPERATURE_METRIC'],
           DEGREE_SYMBOL,
           CONDITIONS['HUMIDITY'],
           CONDITIONS['PARKWIDE']['SO2'],
           CONDITIONS['PARKWIDE']['PM25']
           )
    return result


def makeKey(word):
    return word.replace(' ','_').lower()


def getDotIconId(level):
    ''' Get the clean id for a dot icon and style '''
    if level not in ADVISORY_SCALE:
        level = 'Unknown'
    return makeKey(level) + '_dot'


def buildDotIconUrl(level):
    ''' Build the URL to get the image for a dot icon '''
    return ('%s%s/%s.png') % (SERVER_URL, ICON_PATH, getDotIconId(level))


def getPolyStyleId(level):
    if level not in ADVISORY_SCALE:
        level = 'Unknown'
    ''' Get the clean id for a polygon style '''
    return makeKey(level) + '_poly'


def buildStyles():
    ''' Build the various styles to be used for the placemarks'''
    kmlStyles = []
    for level in ADVISORY_SCALE:
        # build the dot style
        innerIconStyle = styles.IconStyle(NAME_SPACE, scale=.7, icon_href=buildDotIconUrl(level))
        iconStyle = styles.Style(NAME_SPACE, id=getDotIconId(level), styles=[innerIconStyle])
        kmlStyles.append(iconStyle)
        
        # build the polygon style
        innerPolyStyle = styles.PolyStyle(NAME_SPACE, color='33' + ADVISORY_SCALE[level], fill=1, outline=1)
        innerLineStyle = styles.LineStyle(NAME_SPACE, color='FF' + ADVISORY_SCALE[level], width=2)
        polyStyle = styles.Style(NAME_SPACE, id=getPolyStyleId(level), styles=[innerLineStyle, innerPolyStyle])
        kmlStyles.append(polyStyle)
    return kmlStyles

    
def buildSites(folder):
    ''' Iterate through the json data and create visible KML elements for each site.
    '''
    siteData = 'start'
    index = 1
    while siteData is not None:
        key = 'SITE' + str(index)
        siteData = getDataValue(key)
        if siteData:
            buildPlacemarkForSite(folder, siteData)
        index += 1

    
def buildPlacemarkForSite(folder, siteData):
    ''' Build a placemark for a particular site.
        If the site is in PLUME_SOURCES, then show a wedge or circle depending on the wind speed.
        Otherwise show just a point.
        Render a popup or not based on json data.
    '''
    siteName = siteData['name']
    if siteName in SITE_POSITIONS:
        dotPlacemark = kml.Placemark(NAME_SPACE, siteName, siteName, getSiteDescription(siteData))
        dotPlacemark.styleUrl = '#' + getDotIconId(getDataValue('SO2.AQItext', siteData))
        dotPlacemark.geometry = buildPoint(SITE_POSITIONS[siteName], siteName)
        folder.append(dotPlacemark)
        
        if siteName == PLUME_SOURCE:
            plumeData = getPlumeSourceData()
            for crater in WEDGE_POSITIONS:
                craterPlacemark = kml.Placemark(NAME_SPACE, makeKey(crater), crater, getCraterDescription(plumeData))
                craterPlacemark.styleUrl = '#' + getPolyStyleId(getDataValue('SO2.AQItext', plumeData))
                if CONDITIONS['LOW_WIND']:
                    craterPlacemark.geometry = buildCircle(WEDGE_POSITIONS[crater], crater)
                else:
                    craterPlacemark.geometry = buildWedge(WEDGE_POSITIONS[crater], CONDITIONS['WIND_DIRECTION'], crater)
                folder.append(craterPlacemark);


def getSiteDescription(siteData):
    ''' Get printable string to show when the user clicks on a placemark for a site '''
    result = ('%s\n') % getDataValue('name', siteData)
    try:
        if 'SO2' in siteData:
            so2Value = getDataValue('SO2.average15', siteData)
            result += ('SO2: %f ppm\n') % float(so2Value)
    except:
        pass
    try:
        if 'PM25' in siteData:
            pm25Value = int(getDataValue('PM25.average15', siteData))
            result += ('PM25: %d %sg/m3\n') % (pm25Value, unichr(956))
    except:
        pass
    return result


def getCraterDescription(siteData):
    ''' Get printable string of the plume conditions '''
    result = ('%s\nWind Speed: %d mph (%d m/s)\nWind Direction: %d\nTemperature: %d %sF (%d %sC)\nHumidity: %d %%\n%s SO2: %s ppm (%s)\n%s PM25: %s %sg/m3 (%s)')\
        % (getDataValue('datadate'),
           CONDITIONS['WIND_SPEED'],
           CONDITIONS['WIND_SPEED_METRIC'],
           CONDITIONS['WIND_DIRECTION'],
           CONDITIONS['TEMPERATURE'],
           DEGREE_SYMBOL,
           CONDITIONS['TEMPERATURE_METRIC'],
           DEGREE_SYMBOL,
           CONDITIONS['HUMIDITY'],
           PLUME_SOURCE,
           siteData['SO2']['average15'],
           siteData['SO2']['AQItext'],
           PLUME_SOURCE,
           siteData['PM25']['average15'],
           unichr(956),
           siteData['PM25']['AQItext'],
           )
    return result


def buildPoint(location, name):
    pointID = makeKey(name) + '_point'
    alt = 0.0
    if alt in location:
        alt = location['alt']
    pointShape =  Point([(location['lon'], location['lat'], alt)])
    kmlGeometry = geometry.Geometry(NAME_SPACE, id=pointID, geometry=pointShape, extrude=False, tessellate=False, altitude_mode='clampToGround')
    return kmlGeometry


def buildHeading(heading):
    if heading < 0:
        heading += 360
    elif heading > 360:
        heading -= 360
    return heading
        
    
def buildWedge(location, heading, name):
    wedgeID = makeKey(name) + '_wedge'
    centerPoint = LatLon(location['lat'], location['lon'])
    point1 = centerPoint.offset(buildHeading(heading - (WEDGE_ANGLE/2.0)), float(WEDGE_LENGTH))
    point2 = centerPoint.offset(buildHeading(heading + (WEDGE_ANGLE/2.0)), float(WEDGE_LENGTH))
    coords = [(centerPoint.lon.decimal_degree, centerPoint.lat.decimal_degree),
              (point1.lon.decimal_degree, point1.lat.decimal_degree),
              (point2.lon.decimal_degree, point2.lat.decimal_degree)]
    wedgeShape = Polygon(coords)
    kmlGeometry = geometry.Geometry(NAME_SPACE, id=wedgeID, geometry=wedgeShape, extrude=False, tessellate=False, altitude_mode='clampToGround')
    return kmlGeometry


def buildCircle(location, name):
    circleID = makeKey(name) + '_circle'
    boundaryCircle = polycircles.Polycircle(latitude=location['lat'],
                                            longitude=location['lon'],
                                            radius=CIRCLE_RADIUS * 1000,
                                            number_of_vertices=36)
    coords = [(coord[1], coord[0]) for coord in boundaryCircle.vertices]
    circleShape = Polygon(coords) 
    kmlGeometry = geometry.Geometry(NAME_SPACE, id=circleID, geometry=circleShape, extrude=False, tessellate=True, altitude_mode='clampToGround')
    return kmlGeometry


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog --url myserver/hvnp_so2.kml' + 
                                   '--outputDir <dirname> ' +
                                   '--recorderId <recorderID>')
    parser.add_option('-c', '--childKml', dest='childKml', action='store_true',
                      help='True to generate only the child kml with data')
    parser.add_option('-p', '--prefix', dest="prefix", default=SERVER_URL,
                      help='Prefix for server url; Google Earth will hit this server (ie http://hawaiiso2network.com).')
    parser.add_option('-i', '--interval', dest="interval", default=300,
                      help='Refresh interval for network link in seconds')
    parser.add_option('-u', '--url', dest="url",
                      help='Url on your server that will hit this script and generate the child kml')
    
    opts, args = parser.parse_args()
    if len(args) != 0:
        parser.error('expected no arguments')
    if not (opts.prefix):
        parser.error("Prefix option is required.")

    if opts.childKml:
        result = getCurrentStateKml(opts.prefix).encode('utf-8');
        print result
        return result
    else:
        result = buildNetworkLinkKMLFile(opts.prefix + '/' + opts.url, interval=opts.interval).encode('utf-8')
        print result
        return result

if __name__ == '__main__':
    main()