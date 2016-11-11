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
import urllib2
import json
from xml.sax.saxutils import escape
from fastkml import kml, geometry, styles
from shapely.geometry import Point, Polygon
from polycircles import polycircles
from LatLon import LatLon

SERVER_URL = None
RAW_DATA_URL = "http://www.hawaiiso2network.com/havo_json.txt" # source of the json for the data
ADVISORY_SUMMARY_URL = 'http://www.hawaiiso2network.com/summary.html'

# Update this with the path to icons on your server
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
                                    'alt': 1123}}

PLUME_SOURCES = {'Visitor Center',
                 'Jaggar Museum'}

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

def getCurrentStateKml(serverUrl):
    ''' Create the overall KML for the current state of the air quality.
    If we can't get fresh data, return None
    serverUrl = the url of the server providing this KML, so we can have the network link and the icons.
    '''
    
    # Try to get data
    global CURRENT_DATA
    CURRENT_DATA = getData()
    if not CURRENT_DATA:
        return None
    
    global SERVER_URL
    SERVER_URL = serverUrl
    
    # Create the root KML object
    topKml = kml.KML()
    
    # Create a KML Document and add it to the KML root object
    document = kml.Document(NAME_SPACE, 'hvnp_caq_doc', 
                            "Hawai'i Volcanoes National Park", 
                            "Approximate direction of the volcanic gas plumes (wedges) from Halema'uma'u and Pu'u 'O'o. Colored circles show the current air quality conditions for sulfur dioxide and particulate matter at each monitoring site.",
                            styles=buildStyles())

    topKml.append(document)
    
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


def buildNetworkLink(url, name, interval=900):
    ''' Build a Network link to refresh an url every interval seconds
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

def getData():
    ''' Get the json data from the hawaiiso2network website and store it
    '''
    try:
        response = urllib2.urlopen(RAW_DATA_URL)
        return json.load(response)
    except:
        return None


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


def getConditions():
    ''' Interpret the MET block '''
    met = getDataValue('MET')
    CONDITIONS['WIND_SPEED'] = int(met['WS'])
    CONDITIONS['WIND_SPEED_METRIC'] = int(met['WS-metric'])
    CONDITIONS['WIND_DIRECTION'] = int(met['WD'])
    CONDITIONS['TEMPERATURE'] = int(met['AT'])
    CONDITIONS['TEMPERATURE_METRIC'] = int(met['AT-metric'])
    CONDITIONS['LOW_WIND'] = CONDITIONS['WIND_SPEED'] <= int(met['WS-threshold'])
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
    return ('%s%s%s.png') % (SERVER_URL, ICON_PATH, getDotIconId(level))


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
        innerIconStyle = styles.IconStyle(NAME_SPACE, scale=1.0, icon_href=buildDotIconUrl(level))
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
        placemark = kml.Placemark(NAME_SPACE, siteName, siteName, getSiteDescription(siteData))
        if siteName in PLUME_SOURCES:
            placemark.styleUrl = '#' + getPolyStyleId(getDataValue('SO2.AQItext', siteData))
            if CONDITIONS['LOW_WIND']:
                placemark.geometry = buildCircle(SITE_POSITIONS[siteName], siteName)
            else:
                placemark.geometry = buildWedge(SITE_POSITIONS[siteName], CONDITIONS['WIND_DIRECTION'], siteName)
        else:
            placemark.styleUrl = '#' + getDotIconId(getDataValue('SO2.AQItext', siteData))
            placemark.geometry = buildPoint(SITE_POSITIONS[siteName], siteName)
        folder.append(placemark)


def getSiteDescription(siteData):
    ''' Get printable string to show when the user clicks on a placemark for a site '''
    result = ('%s\n') % getDataValue('name', siteData)
    if 'SO2' in siteData:
        result += ('SO2: %f ppm\n') % float(getDataValue('SO2.average15', siteData))
    if 'PM25' in siteData:
        result += ('PM25: %d %sg/m3\n') % (int(getDataValue('PM25.average15', siteData)), unichr(956))
    return result

    
def buildPoint(location, name):
    pointID = makeKey(name) + '_point'
    pointShape =  Point([(location['lon'], location['lat'], location['alt'])])
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
    print coords
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
