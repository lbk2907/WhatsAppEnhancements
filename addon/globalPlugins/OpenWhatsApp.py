# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Clases para abrir la aplicación por Héctor J. Benítez Corredera <xebolax@gmail.com>

import globalPluginHandler
import addonHandler
import gui
import api
import ui
from scriptHandler import script
from winUser import user32
from nvwave import playWaveFile
import shellapi
import globalVars
import wx
import os
import sys
import subprocess
import ctypes
from globalVars import appArgs
from threading import Thread

# translation line
addonHandler.initTranslation()

soundsPath = os.path.join(appArgs.configPath, 'addons', 'WhatsAppEnhancements', 'sounds')

class disable_file_system_redirection:

	_disable = ctypes.windll.kernel32.Wow64DisableWow64FsRedirection
	_revert = ctypes.windll.kernel32.Wow64RevertWow64FsRedirection

	def __enter__(self):
		self.old_value = ctypes.c_long()
		self.success = self._disable(ctypes.byref(self.old_value))

	def __exit__(self, type, value, traceback):
		if self.success:
			self._revert(self.old_value)

def obtenApps():
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	try:
		os.environ['PROGRAMFILES(X86)']
		with disable_file_system_redirection():
			p = subprocess.Popen('PowerShell get-StartApps'.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=si, creationflags = 0x08000000, universal_newlines=True)
	except:
		p = subprocess.Popen('PowerShell get-StartApps'.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=si, creationflags = 0x08000000, universal_newlines=True)
	result_string = str(p.communicate()[0])
	lines = [s.strip() for s in result_string.split('\n') if s]
	nuevo = lines[2:]
	lista_final = []
	for x in nuevo:
		y = ' '.join(x.split())
		z = y.rsplit(' ', 1)
		lista_final.append(z)
	return lista_final

def searchApp(list, value):
	tempA = []
	tempB = []
	for i in range(0, len(list)):
		tempA.append(list[i][0])
		tempB.append(list[i][1])
	filter = [item for item in tempA if value.lower() in item.lower()]
	return tempA, tempB, filter

IS_WinON = False

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Open WhatsApp, or focus it if it is already open')
	)
	def script_open(self, gesture):
		_MainWindows = PluginThread()
		_MainWindows.start()

class ViewApps(wx.Dialog):
	def __init__(self, parent, name, id, results):
		# window title
		super(ViewApps, self).__init__(parent, -1, title=_('app launcher'), size=(350, 150))
		global IS_WinON
		IS_WinON = True
		self.choiceSelection = 0
		self.name = name
		self.id = id
		self.results = results
		self.Panel = wx.Panel(self)
		self.choice = wx.Choice(self.Panel, wx.ID_ANY, choices =["Select a WhatsApp application"] + self.results)
		self.choice.SetSelection(self.choiceSelection)
		self.choice.Bind(wx.EVT_CHOICE, self.onChoiceApp)
		# launch button label
		self.launch = wx.Button(self.Panel, wx.ID_ANY, _('Launch'))
		self.launch.Bind(wx.EVT_BUTTON, self.onLaunch)
		# cancel button label
		self.closeButton = wx.Button(self.Panel, wx.ID_CANCEL, _('Cancel'))
		self.closeButton.Bind(wx.EVT_BUTTON, self.close, id=wx.ID_CANCEL)

		sizerV = wx.BoxSizer(wx.VERTICAL)
		sizerH = wx.BoxSizer(wx.HORIZONTAL)

		sizerV.Add(self.choice, 0, wx.EXPAND | wx.ALL)

		sizerH.Add(self.launch, 2, wx.CENTER)
		sizerH.Add(self.closeButton, 2, wx.CENTER)

		sizerV.Add(sizerH, 0, wx.CENTER)

		self.Panel.SetSizer(sizerV)

		self.CenterOnScreen()

	def onChoiceApp(self, event):
		# app selection title
		if self.choice.GetString(self.choice.GetSelection()) == _('Select one of the WhatsApp applications'):
			self.choiceSelection = 0
		else:
			self.choiceSelection = event.GetSelection()

	def onLaunch(self, event):
		if self.choiceSelection == 0:
			# Application Selection Warning Message
			gui.messageBox(_('You must select an application to continue.'), _("Información"), wx.ICON_INFORMATION)
			self.choice.SetFocus()
		else:
			global IS_WinON
			IS_WinON = False
			shellapi.ShellExecute(None, 'open', "explorer.exe", "shell:appsfolder\{}".format(self.id[self.name.index(self.results[self.choiceSelection - 1])]), None, 10)
			self.Destroy()
			gui.mainFrame.postPopup()

	def close(self, event):
		global IS_WinON
		IS_WinON = False
		self.Destroy()
		gui.mainFrame.postPopup()

class PluginThread(Thread):
	def __init__(self):
		super(PluginThread, self).__init__()
		playWaveFile(os.path.join(soundsPath, 'launching.wav'))

		self.daemon = True

	def run(self):
		def runApp():
			name, id, results = searchApp(obtenApps(), "WhatsApp")
			if len(results) == 1:
				shellapi.ShellExecute(None, 'open', "explorer.exe", "shell:appsfolder\{}".format(id[name.index(results[0])]), None, 10)
			elif len(results) >= 2:
				if IS_WinON == False:
					self._MainWindows = ViewApps(gui.mainFrame, name, id, results)
					gui.mainFrame.prePopup()
					self._MainWindows.Show()
			else:
				# Application not found warning message
				ui.message(_('WhatsApp application not found'))

		wx.CallAfter(runApp)
