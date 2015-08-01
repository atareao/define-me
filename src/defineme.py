#! /usr/bin/python
# -*- coding: iso-8859-15 -*-
#
__author__='Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'
__date__ ='$01-enero-2011 20:00:00$'
#
# A simple application to look up for definitions
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
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import WebKit2
from gi.repository import GdkPixbuf
import os
import sys, re

from urllib.parse import urlencode, urljoin
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

import lxml.html as lh
from lxml.html.clean import clean_html
#
from configurator import Configuration
import comun
from comun import _
from comun import read_from_url, internet_on
#
from preferences import PF
from preferences import urls

'''
def absfile(filename):
	return os.path.join(APPDIR,filename)
'''

def add2menu(menu, text = None, icon = None, conector_event = None, conector_action = None):
	if text != None:
		if icon == None:
			menu_item = Gtk.MenuItem.new_with_label(text)
		else:
			menu_item = Gtk.ImageMenuItem.new_with_label(text)
			image = Gtk.Image.new_from_stock(icon, Gtk.IconSize.MENU)
			menu_item.set_image(image)
			menu_item.set_always_show_image(True)
	else:
		if icon == None:
			menu_item = Gtk.SeparatorMenuItem()
		else:
			menu_item = Gtk.ImageMenuItem.new_from_stock(icon, None)
			menu_item.set_always_show_image(True)
	if conector_event != None and conector_action != None:				
		menu_item.connect(conector_event,conector_action)
	menu_item.show()
	menu.append(menu_item)

class Defineme(Gtk.Dialog): # needs Gtk, Python, Webkit-Gtk
	def __init__(self,busqueda_inicial = None):
		self.last_link = ''
		#
		Gtk.Dialog.__init__(self)
		self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self.set_title('define-me')
		self.set_default_size(600, 400)
		self.set_icon_from_file(comun.ICON)
		self.connect('destroy', self.close_application)
		#
		self.vbox1 = Gtk.VBox(spacing = 5)
		self.vbox1.set_border_width(5)
		self.get_content_area().pack_start(self.vbox1,False,False,0)
		#
		menubar = Gtk.MenuBar()
		################################################################
		filemenu = Gtk.Menu()
		filem = Gtk.MenuItem(_('File'))
		filem.set_submenu(filemenu)
		#
		add2menu(filemenu, text = None, icon = Gtk.STOCK_QUIT, conector_event = 'activate', conector_action = self.on_exit_activate)
		#
		menubar.append(filem)
		################################################################
		fileedit = Gtk.Menu()
		filee = Gtk.MenuItem(_('Edit'))
		filee.set_submenu(fileedit)
		#
		add2menu(fileedit, text = None, icon = Gtk.STOCK_PREFERENCES, conector_event = 'activate', conector_action = self.on_preferences_activate)
		#
		menubar.append(filee)
		################################################################
		fileh = Gtk.MenuItem(_('Help'))
		fileh.set_submenu(self.get_help_menu())
		menubar.append(fileh)
		################################################################
		self.vbox1.pack_start(menubar,False,False,0)
		#
		self.toolbar = Gtk.HBox(spacing=5)
		self.vbox1.pack_start(self.toolbar,False,False,0)	
		#
		self.button1 = Gtk.Button()
		self.button1.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.LEFT, shadow_type=Gtk.ShadowType.OUT))
		self.button1.connect('clicked',self._go_back)
		self.toolbar.pack_start(self.button1,False,False,0)
		#
		self.button2 = Gtk.Button()
		self.button2.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.OUT))
		self.button2.connect('clicked',self._go_forward)
		self.toolbar.pack_start(self.button2,False,False,0)
		#
		self.text = Gtk.Entry()
		self.text.connect('activate',self._open_bar_url)
		self.toolbar.pack_start(self.text,True,True,0)
		#
		self.button3 = Gtk.Button(stock=Gtk.STOCK_FIND)
		self.button3.connect('clicked',self._open_bar_url)
		self.toolbar.pack_start(self.button3,False,False,0)
		# Combobox
		self.combobox = Gtk.ComboBox()
		self.toolbar.pack_start(self.combobox,False,True,0)
		self.model = Gtk.ListStore(str,str)
		################################################################
		self.load_preferences()
		################################################################
		if self.language in urls['wikipedia'].keys():
			self.model.append(['Wikipedia','wikipedia'])
		if self.language in urls['wordreference'].keys():
			self.model.append(['WordReference','wordreference'])
		if self.language in urls['rae'].keys():
			self.model.append(['RAE','rae'])
		if self.language in urls['dictionary.com'].keys():
			self.model.append(['Dictionary.com','dictionary.com'])			
		self.combobox.set_model(self.model)
		cell = Gtk.CellRendererText()
		self.combobox.pack_start(cell,True);
		self.combobox.add_attribute(cell,'text',0)
		self.combobox.set_active(0)
		#
		self.scrolled_window = Gtk.ScrolledWindow()
		self.scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
		self.webview = WebKit2.WebView()
		self.scrolled_window.add(self.webview)
		self.get_content_area().pack_start(self.scrolled_window,True,True,0)
		#
		self.pbar = Gtk.ProgressBar()
		self.status = Gtk.Label()
		hbox2 = Gtk.HBox(False,0)
		hbox2.set_border_width(5)
		hbox2.pack_start(self.status,False,False,0)
		hbox2.pack_end(self.pbar,False,False,0)
		self.get_content_area().pack_start(hbox2,False,False,0)
		
		#
		self.webview.connect('load-changed',self._load_changed)
		
		#self.webview.connect('load-started',self._load_start)
		#self.webview.connect('estimated-load-progress',self._load_progress_changed)
		#self.webview.connect('load-finished',self._load_finished)
		
		self.webview.connect('notify::title',self._title_changed)
		self.webview.connect('mouse-target-changed',self._hover_link)	
		self.webview.connect('decide-policy', self._navigation_requested_cb)
		#self.webview.connect('resource-load-started', self._navigation_requested_cb)
		#
		# Inicializations
		#
		self.loading = False
		self.navigation = []
		self.whereiam = 0
		self.button1.set_sensitive(False)
		self.button2.set_sensitive(False)
		#
		#
		#
		itera = self.model.get_iter_first()
		while itera != None:
			if self.model.get_value(itera,1) == self.dictionary:
				break					
			itera = self.model.iter_next(itera)
		if itera != None:
			self.combobox.set_active_iter(itera)
		else:
			self.combobox.set_active(0)
		#
		self.show_all()
		#
		#
		#
		if busqueda_inicial!= None:
			self._load(busqueda_inicial)
			self.text.set_text(busqueda_inicial)
				 
	def _navigation_requested_cb(self,view, policyDecision,policyDecisionType):
		print('..........................................')
		print('Navigation requested')
		print(policyDecision)
		print(policyDecisionType)
		print('..........................................')
		if policyDecisionType == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
			uri = policyDecision.get_request().get_uri()
			print(uri)
			if self.loading ==False:
				self._loader(uri)
				dictionary = self.combobox.get_model().get_value(self.combobox.get_active_iter(),0)
				self.navigation.append({'language':self.language,'dictionary':dictionary,'word':self.text.get_text()})
				self.whereiam = self.whereiam + 1
				if self.whereiam > 1:
					self.button1.set_sensitive(True)
				return 0
		return 1

	def _open_bar_url(self, nada):
		self.open(self.text.get_text())
	
	def _loader(self,uri):
		if uri != None:
			self.loading = True
			#try:
			print(uri,urls['wikipedia'][self.language])
			if urls['wikipedia'][self.language] is not None and uri.startswith(urls['wikipedia'][self.language]):
				code = read_from_url(uri).decode()
				doc = lh.document_fromstring(clean_html(code))
				result = lh.tostring(doc.get_element_by_id('bodyContent'),method = 'html').decode()
				#self.webview.load_string(result, 'text/html', 'utf-8', uri)
				self.webview.load_html(result, uri)
				self.text.set_text(uri.split(urls['wikipedia'][self.language])[1])
			elif uri.startswith(urls['wordreference'][self.language]):
				code = read_from_url(uri).decode()
				doc = lh.document_fromstring(clean_html(code))
				trans = doc.find_class('trans')
				if len(trans)>0:
					trans_tmp = ''
					for t in trans:
						trans_tmp = trans_tmp + lh.tostring(t,method = 'html').decode()
					self.webview.load_string(trans_tmp, 'text/html', 'utf-8', uri)
					self.text.set_text(uri.split(urls['wordreference'][self.language])[1])	
				else:
					raise HTTPError(uri, '404', '404', None, None)
			elif urls['dictionary.com']['es'] is not None and uri.startswith(urls['dictionary.com']['es']):
				code = read_from_url(uri).decode()
				doc = lh.document_fromstring(clean_html(code))
				body = doc.find_class('tab_contents tab_contents_active')
				if len(body)>0:
					body_tmp = ''
					for b in body:
						body_tmp = body_tmp + lh.tostring(b,method = 'html').decode()
					self.webview.load_string(body_tmp, 'text/html', 'utf-8', uri)
					self.text.set_text(uri.split(urls['dictionary.com'][self.language])[1])
			elif urls['dictionary.com']['en'] is not None and uri.startswith(urls['dictionary.com']['en']):
				code = read_from_url(uri).decode()
				doc = lh.document_fromstring(clean_html(code))
				body = doc.find_class('sep_top shd_hdr pb7')
				if len(body)>0:
					body_tmp = ''
					for b in body:
						body_tmp = body_tmp + lh.tostring(b,method = 'html').decode()
					self.webview.load_string(body_tmp, 'text/html', 'utf-8', uri)
					self.text.set_text(uri.split(urls['dictionary.com'][self.language])[1],encoding)
			elif urls['rae'][self.language] is not None and uri.startswith(urls['rae'][self.language]):
				searchfor = uri.replace(urls['rae'][self.language],'')
				body = self.search_in_rae(searchfor).decode()	
				body = clean_html(body)
				self.webview.load_string(body, 'text/html', 'utf-8', uri)
				self.text.set_text(uri.split(urls['rae'][self.language])[1])	
			elif uri.startswith('http://buscon.rae.es/draeI/search?id='):
				searchfor = uri.replace('http://buscon.rae.es/draeI/search?id=','')
				body = self.search_in_rae_id(searchfor).decode()				
				#pos = body.find('<span class="f"><b>')
				#body = body[pos:]
				body = clean_html(body)
				m = re.search(r'<span class="(.*?)</span>', body, flags=0)
				if m:
					ans = m.group()
					print(ans)
					ans = ans.replace('<b>','').replace('</b>','').replace('</a>','').replace('</span>','')
					ans = ans.split('>')[-1]
					print(ans)
					self.text.set_text(ans)
				self.webview.load_string(body, 'text/html', 'utf-8', uri)
			self.loading = False

	def _load(self, texto):
		searchfor = None
		texto = texto.strip()
		if texto.find(' ')>-1:
			texto = texto.replace(' ','%20')
		model = self.combobox.get_model()
		dictionary = self.combobox.get_model().get_value(self.combobox.get_active_iter(),0)
		if dictionary == 'Wikipedia':
			searchfor = urls['wikipedia'][self.language] + texto
		elif dictionary == 'WordReference':
			searchfor = urls['wordreference'][self.language] + texto
		elif dictionary == 'RAE':
			searchfor = urls['rae'][self.language]+texto
		elif dictionary == 'Dictionary.com':
			searchfor = urls['dictionary.com'][self.language] + texto
		if searchfor != None:
			self._loader(searchfor)
			
	def open(self, url):
		self._load(url)
		
	def show(self):
		self.window.show_all()
		
	def close_application(self, widget, event, data=None):
		exit(0)
		
	def _load_start(self, view, nadas):
		self.status.set_text('Cargando...')
		self.pbar.set_fraction(0)
	
	def _load_changed(self,view,event):
		if(event==WebKit2.LoadEvent.STARTED):
			self.status.set_text('Cargando...')
			self.pbar.set_fraction(0)
		elif(event==WebKit2.LoadEvent.FINISHED):
			self.pbar.set_fraction(0)
			self.status.set_text('Listo')
		'''
		elif(event==WebKit2.LoadEvent.REDIRECTED):
			print('REDIRECTED')
		elif(event==WebKit2.LoadEvent.COMMITTED):			
			print('COMMITTED')
		'''
		
	def _load_progress_changed(self, view, prog):
		self.pbar.set_fraction(prog/100.0)
	
	def _load_finished(self, view, frame):
		self.pbar.set_fraction(0)
		self.status.set_text('Listo')
	
	def _go_back(self,nada):
		if len(self.navigation)>0 and self.whereiam > 0:
			self.whereiam = self.whereiam -1
			self.language = self.navigation[self.whereiam]['language']
			dictionary = self.navigation[self.whereiam]['dictionary']
			if dictionary == 'Wikipedia':
				self.combobox.set_active(0)
			elif dictionary == 'WordReference':
				self.combobox.set_active(1)
			elif dictionary == 'RAE':
				self.combobox.set_active(2)
			elif dictionary == 'Dictionary.com':
				self.combobox.set_active(3)				
			word = self.navigation[self.whereiam]['word']
			self._load(word)
		if self.whereiam >0:
			self.button1.set_sensitive(True)
		else:
			self.button1.set_sensitive(False)
		if self.whereiam < (len(self.navigation)-2):
			self.button2.set_sensitive(True)
		else:
			self.button2.set_sensitive(False)
	
	def _go_forward(self,nada):
		if len(self.navigation)>0 and self.whereiam < (len(self.navigation)-1):
			self.whereiam = self.whereiam + 1
			self.language = self.navigation[self.whereiam]['language']
			dictionary = self.navigation[self.whereiam]['dictionary']
			if dictionary == 'Wikipedia':
				self.combobox.set_active(0)
			elif dictionary == 'WordReference':
				self.combobox.set_active(1)
			elif dictionary == 'RAE':
				self.combobox.set_active(2)
			elif dictionary == 'Dictionary.com':
				self.combobox.set_active(3)
			word = self.navigation[self.whereiam]['word']
			self._load(word)
		if self.whereiam >0:
			self.button1.set_sensitive(True)
		else:
			self.button1.set_sensitive(False)
		if self.whereiam < (len(Self.navigation)-2):
			self.button2.set_sensitive(True)
		else:
			self.button2.set_sensitive(False)

	
	def _refresh(self,nada):
		self.webview.reload()
	
	def _title_changed(self,view,title):
		# Actualizo el titulo del navegador, la url en la barra de url y activo/desactivo los botones Adelante y Atras
		self.set_title('%s' % self.webview.get_title())
		self.button1.props.sensitive = self.webview.can_go_back()
		self.button2.props.sensitive = self.webview.can_go_forward()
	
	def _hover_link(self,view,hittestresult,data):
		if hittestresult.context_is_link():
			url = hittestresult.get_link_uri()
			print('............................')
			print(url)
			print(hittestresult)
			print('............................')
			# Si se hace hover sobre un link, pongo en la barra de estado la url hacia la que linkea
			buscador =self.model.get_value(self.combobox.get_active_iter(),1)
			if view and url and buscador == 'wikipedia':
				#self.status.set_text(url)
				self.status.set_text(url.split('/')[-1:][0])
			elif view and url and buscador == 'wordreference':
				pass
			elif view and url and buscador == 'dictionary.com':
				pass
			elif view and url and buscador == 'rae' and url.find('http://buscon.rae.es/draeI/search?id=')>-1:
				title = self.get_title()
				view.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
				html = view.get_main_frame().get_title()
				view.execute_script('document.title=oldtitle;')
				self.set_title(title)
				sf = url.replace('http://buscon.rae.es/draeI/search?id=','')	
				m = re.search(r'<a href="search\?id=%s(.*?)</a>'%sf,html, flags=0)
				if m:
					ans = m.group().replace('<b>','').replace('</b>','').replace('</a>','').replace('</span>','')
					ans = ans.split('>')[-1]
					self.last_link = ans
					self.status.set_text(ans)
				else:
					print(html)
			else:
				self.status.set_text('')
	def on_exit_activate(self,widget):
		exit(0)

	def on_preferences_activate(self,widget):
		pf = PF(self)
		self.load_preferences()
		#
		self.model.clear()
		if self.language in urls['wikipedia'].keys():
			self.model.append(['Wikipedia','wikipedia'])
		if self.language in urls['wordreference'].keys():
			self.model.append(['WordReference','wordreference'])
		if self.language in urls['rae'].keys():
			self.model.append(['RAE','rae'])
		if self.language in urls['dictionary.com'].keys():
			self.model.append(['Dictionary.com','dictionary.com'])
		#
		itera = self.model.get_iter_first()
		while itera != None:
			if self.model.get_value(itera,0) == self.dictionary:
				break					
			itera = self.model.iter_next(itera)
		if itera != None:
			self.combobox.set_active_iter(itera)
		else:
			self.combobox.set_active(0)
	def load_preferences(self):
		configuration = Configuration()
		self.language = configuration.get('language')
		self.dictionary = configuration.get('dictionary')
			
	def get_help_menu(self):
		help_menu =Gtk.Menu()
		#		
		add2menu(help_menu,text = _('Application Web...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://launchpad.net/my-weather-indicator'))
		add2menu(help_menu,text = _('Get help online...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://answers.launchpad.net/my-weather-indicator'))
		add2menu(help_menu,text = _('Translate this application...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://translations.launchpad.net/my-weather-indicator'))
		add2menu(help_menu,text = _('Report a bug...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://bugs.launchpad.net/my-weather-indicator'))
		add2menu(help_menu)
		add2menu(help_menu,text = _('About'),conector_event = 'activate',conector_action = self.on_about_activate)
		#
		help_menu.show()
		#
		return help_menu
		
	def on_about_activate(self,widget):
		ad=Gtk.AboutDialog()
		ad.set_name(comun.APPNAME)
		ad.set_version(comu.VERSION)
		ad.set_copyright('Copyright (c) 2011\nLorenzo Carbonell')
		ad.set_comments(_('A simple application to find the definition of words'))
		ad.set_license(''+
		'This program is free software: you can redistribute it and/or modify it\n'+
		'under the terms of the GNU General Public License as published by the\n'+
		'Free Software Foundation, either version 3 of the License, or (at your option)\n'+
		'any later version.\n\n'+
		'This program is distributed in the hope that it will be useful, but\n'+
		'WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY\n'+
		'or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for\n'+
		'more details.\n\n'+
		'You should have received a copy of the GNU General Public License along with\n'+
		'this program.  If not, see <http://www.gnu.org/licenses/>.')
		ad.set_website('http://www.atareao.es')
		ad.set_website_label('http://www.atareao.es')
		ad.set_authors(['Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
		ad.set_documenters(['Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'])
		ad.set_translator_credits('Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>')		
		ad.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
		ad.set_icon(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
		ad.set_program_name(comun.APPNAME)
		ad.run()
		ad.hide()
	def search_in_rae(self,search_for):
		search_for = search_for.encode('iso-8859-1')  # necessary for rae server
		params = {
			'type': '3',
			'val_aux': '',
			'origen': 'RAE',
		}
		params.update({'val': search_for})
		qs = urlencode(params)
		url = '{0}?{1}'.format('http://lema.rae.es/drae/srv/search', qs)
		try:
			response = urlopen(url)
		except HTTPError as e:
			html = '<html><body><h2>Error</h2><p>Sin conexión</p></body></html>'
		except URLError as e:
			html = '<html><body><h2>Error</h2><p>Sin respuesta</p></body></html>'
		else:
			html = response.read()
		return html

	def search_in_rae_id(self,search_for):
		search_for = search_for.encode('iso-8859-1')  # necessary for rae server
		params = {
			'type': '3',
			'val_aux': '',
			'origen': 'RAE',
		}
		params.update({'id': search_for})
		qs = urlencode(params)
		url = '{0}?{1}'.format('http://buscon.rae.es/drae/srv/search',qs)
		try:
			response = urlopen(url)
		except HTTPError as e:
			html = '<html><body><h2>Error</h2><p>Sin conexión</p></body></html>'
		except URLError as e:
			html = '<html><body><h2>Error</h2><p>Sin respuesta</p></body></html>'
		else:
			html = response.read()
		return html

if __name__ == '__main__':
	sm = Defineme()
	sm.run()

	'''
	#pattern = '<a href="search?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="[a-zA-Z]"><b>[a-zA-Z0-9_]*</b></span></a>'
	pattern = r'<a href="search?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="f"><b>(.*)</b></span></a>'
	#p = re.compile(r'<a href="search?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="f"><b>(.*)</b></span></a>')
	p = re.compile(r'<a href="search\?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="(.*)"><b>(.*)</b></span></a>')
	cadena = '<a href="search?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="f"><b>fdafdafdafda</b></span></a>'
	#cadena = 'sgfsgfs <a href="search?id=ukNZpF0zwDXX2N5Zp136#1_2"><span class="f"><b>agfs</b></span></a> gfsgfsgfs'
	m = p.match(cadena)
	if m:
		print(m.groups())
	p = re.compile(r'(.*)')
	m = p.match('ababababab')
	print(m.groups())
	'''
