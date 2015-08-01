#! /usr/bin/python
# -*- coding: iso-8859-1 -*-
#
__author__="atareao"
__date__ ="$09-jul-2011$"
#
# com.py
#
# Copyright (C) 2011 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#
__author__ = 'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'
__date__ ='$09/07/2011'
__copyright__ = 'Copyright (c) 2011 Lorenzo Carbonell'
__license__ = 'GPLV3'
__url__ = 'http://www.atareao.es'
__version__ = '0.3.1.2'

import sys
import os
import locale
import gettext

######################################

def is_package():
    return __file__.find('src') < 0

######################################


APP = 'define-me'
APPNAME = 'Define-Me'
ICONNAME = 'define-me.svg'
PARAMS = {'language':'en',
		  'dictionary':'wikipedia',
		}

# check if running from source
if is_package():
    ROOTDIR = '/opt/extras.ubuntu.com/%s/share/'%APP
    LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
    APPDIR = os.path.join(ROOTDIR, APP)
    ICON = os.path.join('/opt/extras.ubuntu.com/%s/share/pixmaps'%APP,ICONNAME)
    CHANGELOG = os.path.join(APPDIR,'changelog')
else:
    ROOTDIR = os.path.dirname(__file__)
    LANGDIR = os.path.normpath(os.path.join(ROOTDIR, '../template1'))
    DATADIR = os.path.normpath(os.path.join(ROOTDIR, '../data'))
    ICON = os.path.join(DATADIR,ICONNAME)
    APPDIR = ROOTDIR
    DEBIANDIR = os.path.normpath(os.path.join(ROOTDIR, '../debian'))
    CHANGELOG = os.path.join(DEBIANDIR,'changelog')

APP_CONF = APP + '.conf'
CONFIG_DIR = os.path.join(os.path.expanduser('~'),'.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APP_CONF)

f = open(CHANGELOG,'r')
line = f.readline()
f.close()
pos=line.find('(')
posf=line.find('-',pos)
VERSION = line[pos+1:posf].strip()
if not is_package():
	VERSION = VERSION + '-src'

try:
	current_locale, encoding = locale.getdefaultlocale()
	language = gettext.translation(APP, LANGDIR, [current_locale])
	language.install()
	print(language)
	if sys.version_info[0] == 3:
		_ = language.gettext
	else:
		_ = language.ugettext
except Exception as e:
	print(e)
	_ = str
if sys.version_info[0] == 3:	
	import urllib.request
	def read_from_url(url):
		url = url.replace(' ','%20')
		request = urllib.request.Request(url, headers={'User-Agent' : 'Magic Browser'})
		f = urllib.request.urlopen(request)
		json_string = f.read()
		f.close()
		return json_string

	def internet_on():
		try:
			response=urllib.request.urlopen('http://google.com',timeout=1)
			return True
		except:
			pass
		return False
	def fromunicode(cadena):
		return cadena
else:
	import urllib2
	import urllib	
	def read_from_url(url):
		url = url.replace(' ','%20')
		headers = {
			'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
			'Accept' : 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
			'Accept-Language' : 'es-es,fr-fr,en-us;q=0.7,en;q=0.3',
			'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
		}
		request = urllib2.Request(url, headers=headers)
		f = urllib2.urlopen(request)
		json_string = f.read()
		f.close()
		return json_string
		
	def internet_on():
		try:
			response=urllib2.urlopen('http://google.com',timeout=1)
			return True
		except:
			pass
		return False
	def fromunicode(cadena):
		if type(cadena) == unicode:
			ans = cadena.encode('utf-8')
			print(type(ans),ans)
			return ans
		return cadena
