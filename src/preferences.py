#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject

import sys, re
import locale
import gettext
import comun
from configurator import Configuration

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(comun.APP, comun.LANGDIR)
gettext.textdomain(comun.APP)
_ = gettext.gettext

languages = {}
languages[_('Deutch')]='de'
languages[_('English')]='en'
languages[_('French')]='fr'
languages[_('Spanish')]='es'
languages[_('Italian')]='it'

codes = {}
codes['de'] = _('Deutch')
codes['en'] = _('English')
codes['fr'] = _('French')
codes['es'] = _('Spanish')
codes['it'] = _('Italian')


urls = {}

urls['wikipedia'] = {'es':'http://es.wikipedia.org/wiki/',
					'en':'http://en.wikipedia.org/wiki/',
					'fr':'http://fr.wikipedia.org/wiki/',
					'it':'http://it.wikipedia.org/wiki/',
					'de':'http://de.wikipedia.org/wiki/'}
urls['wordreference'] = {'es':'http://www.wordreference.com/definicion/',
						'en':'http://www.wordreference.com/definition/',
						'fr':None,
						'it':'http://www.wordreference.com/definizione/',
						'de':None}
#urls['rae'] = {'es':'http://buscon.rae.es/draeI/SrvltGUIBusUsual?origen=RAE&LEMA='}
#urls['rae'] = {'es':'http://lema.rae.es/drae/?val='}
urls['rae'] = {'es':'http://buscon.rae.es/draeI/SrvltGUIBusUsual?LEMA=',
			   'en':None,
			   'fr':None,
			   'it':None,
			   'de':None}
#urls['rae'] = {'es':'http://lema.rae.es/drae/srv/search?val='}
#urls['rae'] = {'es':'http://buscon.rae.es/draeI/SrvltConsulta?TIPO_BUS=3&LEMA='}
urls['dictionary.com'] = {'es':'http://spanish.dictionary.com/definition/',
				'en':'http://dictionary.reference.com/browse/',
				'fr':None,
				'it':None,
				'de':None}
							  


class PF(Gtk.Dialog): # needs Gtk, Python, Webkit-Gtk
	def __init__(self,parent):
		Gtk.Dialog.__init__(self)
		title = comun.APPNAME + ' | '+_('Preferences')
		Gtk.Dialog.__init__(self, title,parent,Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
		self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self.connect('destroy', self.close_application)
		#
		frame = Gtk.Frame()
		self.get_content_area().add(frame)
		vbox1 = Gtk.VBox(spacing = 5)
		vbox1.set_border_width(5)
		frame.add(vbox1)
		#
		hbox1 = Gtk.HBox(spacing=5)
		vbox1.pack_start(hbox1,False,False,0)
		#
		label1 = Gtk.Label(_('Language')+': ')
		hbox1.pack_start(label1,False,False,0)
		#
		self.combobox1 = Gtk.ComboBox()
		self.model1 = Gtk.ListStore(str,str)
		for language in languages:
			self.model1.append([language,languages[language]])
		self.combobox1.set_model(self.model1)
		cell1 = Gtk.CellRendererText()
		self.combobox1.pack_start(cell1,True);
		self.combobox1.add_attribute(cell1,'text',0)
		self.combobox1.set_active(0)
		self.combobox1.connect('changed',self.on_selection_changed)
		hbox1.pack_start(self.combobox1,True,True,0)
		#
		hbox2 = Gtk.HBox(spacing=5)
		vbox1.pack_start(hbox2,False,False,0)
		#
		label2 = Gtk.Label(_('Prefered')+': ')
		hbox2.pack_start(label2,False,False,0)
		#
		self.combobox2 = Gtk.ComboBox()
		self.model2 = Gtk.ListStore(str,str)
		self.model2.append(['Wikipedia','wikipedia'])
		self.model2.append(['WordReference','wordreference'])
		self.model2.append(['RAE','rae'])
		self.model2.append(['Dictionary.com','dictionary.com'])
		self.combobox2.set_model(self.model2)
		cell2 = Gtk.CellRendererText()
		self.combobox2.pack_start(cell2,True);
		self.combobox2.add_attribute(cell2,'text',0)
		self.combobox2.set_active(0)
		hbox2.pack_start(self.combobox2,True,True,0)
		#
		self.load_preferences()
		#
		self.show_all()
		#
		if self.run() == Gtk.ResponseType.ACCEPT:
			self.save_preferences()
		self.destroy()
		
	
	def close_application(self, widget, data=None):
		self.hide()
	
	def on_selection_changed(self,widget):
		self.model2.clear()
		language_iter = self.combobox1.get_active_iter()
		language = self.model1.get_value(language_iter,1)
		if language in urls['wikipedia'].keys():
			self.model2.append(['Wikipedia','wikipedia'])
		if language in urls['wordreference'].keys():
			self.model2.append(['WordReference','wordreference'])
		if language in urls['rae'].keys():
			self.model2.append(['RAE','rae'])
		if language in urls['dictionary.com'].keys():
			self.model2.append(['Dictionary.com','dictionary.com'])
		self.combobox2.set_active(0)

	def load_preferences(self):
		configuration = Configuration()
		language = configuration.get('language')
		dictionary = configuration.get('dictionary')
		print(language)
		print(dictionary)
		itera = self.model1.get_iter_first()
		while itera != None:
			if self.model1.get_value(itera,1) == language:
				break					
			itera = self.model1.iter_next(itera)
		if itera != None:
			self.combobox1.set_active_iter(itera)
		else:
			self.combobox1.set_active(0)
		itera = self.model2.get_iter_first()
		while itera != None:
			if self.model2.get_value(itera,1) == dictionary:
				break					
			itera = self.model2.iter_next(itera)
		if itera != None:
			self.combobox2.set_active_iter(itera)
		else:
			self.combobox2.set_active(0)		
		
	def save_preferences(self):
		configuration = Configuration()
		language = self.model1.get_value(self.combobox1.get_active_iter(),1)
		dictionary = self.model2.get_value(self.combobox2.get_active_iter(),1)
		configuration.set('language',language)
		configuration.set('dictionary',dictionary)
		configuration.save()
		
if __name__ == '__main__':
	pf = PF(None)
	exit(0)

