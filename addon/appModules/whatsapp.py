# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

from threading import Thread
from time import sleep
import speech
from globalVars import appArgs
import appModuleHandler
from scriptHandler import script
import wx
import api
from ui import message
from nvwave import playWaveFile
from re import search, sub
import os
import addonHandler

# Translation Line
addonHandler.initTranslation()

def mute(time, msg= False):
	if msg:
		message(msg)
		sleep(0.1)
	Thread(target=killSpeak, args=(time,), daemon= True).start()

# Function to break the speech chain and silence the synthesizer for the specified time
def killSpeak(time):
	speech.setSpeechMode(speech.SpeechMode.off)
	sleep(time)
	speech.setSpeechMode(speech.SpeechMode.talk)

class AppModule(appModuleHandler.AppModule):
	# Category name in input gestures dialog
	category = _('WhatsApp Enhancements')

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		# Message announcing that an element was not found
		self.notFound = _('Item not found')
		self.lastChat = None
		self.soundsPath = os.path.join(appArgs.configPath, 'addons', 'WhatsAppEnhancements', 'sounds')
		self.configFile()

	def configFile(self):
		try:
			with open(f'{appArgs.configPath}\\WhatsAppEnhancements.ini', 'r') as f:
				self.viewConfig = f.read()
		except FileNotFoundError:
			with open(f'{appArgs.configPath}\\WhatsAppEnhancements.ini', 'w') as f:
				f.write('enabled')

	# Function that receives the UIAAutomationId by parameter, and returns the match object
	def get(self, id, errorMessage, gesture):
		for obj in api.getForegroundObject().children[1].children:
			if obj.UIAAutomationId == id:
				return obj#
		if errorMessage:
			message(self.notFound)
		if gesture:
			gesture.send()

	def event_NVDAObject_init(self, obj):
		try:
			if obj.UIAAutomationId == 'BackButton':
				obj.name = _('Back')
			elif obj.UIAAutomationId == 'CloseButton':
				obj.name = _('Cancel')
			elif obj.name == '\ue8bb':
				obj.name = _('Cancel reply')
			elif obj.name == '\ue76e':
				obj.name = 'React to message'
			elif obj.UIAAutomationId == 'SendMessages':
				obj.name = '{}: {}'.format(obj.previous.name, obj.firstChild.name)
			elif obj.UIAAutomationId == 'EditInfo':
				obj.name = '{}: {}'.format(obj.previous.name, obj.firstChild.name)
			elif obj.UIAAutomationId == 'ThemeCombobox':
				obj.name = obj.previous.name + obj.firstChild.children[1].name
			elif obj.name == 'WhatsApp.Design.ThemeData':
				obj.name = obj.children[1].name
			elif obj.UIAAutomationId == 'NewMessagesNotificationSwitch':
				obj.name = '{}:  {}'.format(obj.previous.name, obj.name)
			elif obj.UIAAutomationId == 'WhenWAClosedSwitch':
				obj.name = '{}:  {}'.format(obj.previous.name, obj.name)
			elif obj.UIAAutomationId == "MuteDropdown":
				obj.name = obj.children[0].name
			if obj.name in ("WhatsApp.WaCollections.KeyedObservableCollection`2[WhatsApp.GroupItem,WhatsApp.RecipientItem]", "WhatsApp.RecipientItem", "WhatsApp.ReceiptViewModel",):
				obj.name = ", ".join([m.name for m in obj.children])
			if obj.name == 'WhatsApp.PeerStreamVm':
				if obj.firstChild.children[1].name == 'Ringing...':
					obj.name = '{}, {}'.format(obj.firstChild.children[0].name, obj.firstChild.children[1].name)
				elif obj.firstChild.children[2].name == 'Muted':
					obj.name = '{}, {}, {}'.format(obj.firstChild.children[0].name, obj.firstChild.children[2].name, obj.firstChild.children[3].name)
				else:
					obj.name = _('{}, unmuted, {}'.format(obj.firstChild.children[0].name, obj.firstChild.children[2].name))
			elif obj.UIAAutomationId in ('CancelButton', 'RejectButton'):	
				obj.name = obj.firstChild.name
			elif obj.UIAAutomationId == 'AcceptButton':
				obj.name = obj.children[1].name
			elif obj.name in ('WhatsApp.ViewModels.EmojiPickerCategoryViewModel', 'WhatsApp.Pages.Recipients.RecipientGroupingVm`1[WhatsApp.Pages.Recipients.ForwardMessageVm+IItem]'):
				obj.name = obj.firstChild.name
		except:
			pass
		try:
			if self.viewConfig == 'enabled': return
			if obj.UIAAutomationId == 'BubbleListItem':
				obj.name = sub(r'‪\+\d[()\d\s‬-]{12,}', '', obj.name)
		except:
			pass

	def event_gainFocus(self, obj, nextHandler):
		try:
			# Rename the message with attached document by the text of the objects that have the file name, type and size
			if obj.UIAAutomationId == 'BubbleListItem':
				for i in range(1, 9):
					if obj.children[i].UIAAutomationId == 'NameTextBlock':
						for data in obj.children:
							if data.UIAAutomationId == 'NameTextBlock':
								obj.name = '{}, {}, {}'.format(data.name, data.next.name, data.next.next.next.next.name)
					if obj.children[i].UIAAutomationId == 'ReactionBubble':
						for data in obj.children:
							if data.UIAAutomationId == 'ReactionBubble':
								obj.name = '{}. Reaction available.'.format(obj.name)
#					elif obj.children[i].UIAAutomationId == 'NameTextBlock' and obj.children[i].UIAAutomationId == 'ReactionBubble':
#						for data in obj.children:
#							if data.UIAAutomationId == 'NameTextBlock' and data.UIAAutomationId == 'ReactionBubble':
#								obj.name = '{}. Extra information available. Reaction available.'.format(obj.name)
#				for i in range(1, 9):
#					elif obj.children[i].UIAAutomationId == 'ReactionBubble':
#						for data in obj.children:
#							if data.UIAAutomationId == 'ReactionBubble':
#						obj.name = '{}, {}'.format(data.name, data.next.name)
#								obj.name = '{}'.format(data.name)
			else:
				nextHandler()
		except:
			nextHandler()
		try:
			if obj.UIAAutomationId == 'ChatsListItem':
				self.lastChat = obj
			else:
				nextHandler()
		except:
			nextHandler()

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Create new conversation'),
		gesture= 'kb:control+n'
	)
	def script_newChat(self, gesture):
		newChat = self.get('NewConvoButton', False, None)
		if newChat:
			message(newChat.name)
			newChat.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('More option'),
		gesture= 'kb:alt+o'
	)
	def script_settings(self, gesture):
		settings = self.get('SettingsButton', False, None)
		if settings:
			message(settings.name)
			settings.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Press the back button in the archived chats window and the close button for the search in message'),
		gesture= 'kb:alt+b'
	)
	def script_backAndCloseButton(self, gesture):
		backButton = self.get('BackButton', False, None)
		closeButton = self.get('CloseButton', False, None)
		if backButton:
			backButton.doAction()
		elif closeButton:
			closeButton.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Focus on the chat list'),
		gesture= 'kb:alt+c'
	)
	def script_chatsList(self, gesture):
		chatList = self.get('ChatList', False, None)
		if chatList:
			chatList.firstChild.children[0].setFocus()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Focus on the last message in the message list'),
		gesture= 'kb:alt+m'
	)
	def script_messagesList(self, gesture):
		listView = self.get('ListView', False, None)
		if listView:
			listView.lastChild.setFocus()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Go to the first unread message in the message list'),
		gesture= 'kb:alt+u'
	)
	def script_unread(self, gesture):
		def search(txt):
			words = ['غير مقرو', 'unread', 'непрочитанное сообщение', 'Непрочитано', 'непрочитанных сообщений', 'Непрочитане']
			for word in words:
				if txt.find(word) != -1:
					return word
			return -1
		listView = self.get('ListView', False, None)
		if listView:
			for msg in listView.children[::-1]:
				if len(msg.children) == 1 and search(msg.name) != -1:
					msg.next.setFocus()
					break
			else:
				message('There\'s no unread messages')

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Read the chat subtitle'),
		gesture= 'kb:alt+t'
	)
	def script_chatName(self, gesture):
		title = self.get('TitleButton', False, None)
		if title:
			message(', '.join([obj.name.strip() for obj in title.children if len(obj.name) < 50]))
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Conversation info'),
		gesture= 'kb:alt+i'
	)
	def script_moreInfo(self, gesture):
		info = self.get('TitleButton', False, None)
		if info:
			message(info.name)
			info.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Go to the typing message text field'),
		gesture= 'kb:alt+e'
	)
	def script_messageField(self, gesture):
		textBox = self.get('TextBox', False, None)
		if textBox:
			textBox.setFocus()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Add attachment'),
		gesture= 'kb:control+shift+a'
	)
	def script_attach(self, gesture):
		attach = self.get('AttachButton', False, None)
		if attach:
			message(attach.name)
			attach.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Add emoji'),
		gesture= 'kb:control+shift+e'
	)
	def script_emoji(self, gesture):
		emoji = self.get('EmojiButton', False, None)
		if emoji:
			message(emoji.name)
			emoji.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Record and send voice message'),
		gesture= 'kb:control+r'
	)
	def script_record(self, gesture):
		record = self.get('RightButton', False, None)
		send = self.get('PttSendButton', False, None)
		if record:
			record.doAction()
			mute(1)
			playWaveFile(os.path.join(self.soundsPath, 'wa_ptt_start_record.wav'))
		elif send:
			send.doAction()
			playWaveFile(os.path.join(self.soundsPath, 'wa_ptt_sent.wav'))
		else:
			message(self.notFound)

	@script(
	category= 'WhatsAppEnhancements',
	# Item Description in Input Gestures Dialog
	description= _('Pause and resume recording'),
		gesture= 'kb:alt+r'
	)
	def script_pause(self, gesture):
		pause = self.get('PttPauseButton', False, None)
		resume = self.get('PttResumeButton', False, None)
		if pause:
			pause.doAction()
			playWaveFile(os.path.join(self.soundsPath, 'wa_ptt_stop_record.wav'))
		elif resume:
			resume.doAction()
			mute(1)
			playWaveFile(os.path.join(self.soundsPath, 'wa_ptt_start_record.wav'))
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Discard voice message'),
		gesture= 'kb:control+shift+r'
	)
	def script_cancelVoiceMessage(self, gesture):
		cancel = self.get('PttDeleteButton', False, None)
		if cancel:
			cancel.doAction()
			playWaveFile(os.path.join(self.soundsPath, 'wa_ptt_quick_cancel.wav'))
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Report the recording time when recording voice message'),
		gesture= 'kb:control+t'
	)
	def script_timeAnnounce(self, gesture):
		timer = self.get('PttTimer', False, None)
		if timer:
			message(timer.name)
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Audio call'),
		gesture= 'kb:control+shift+c'
	)
	def script_audioCall(self, gesture):
		name = self.get('TitleButton', False, None)
		audioCall = self.get('AudioCallButton', True, gesture)
		if audioCall:
			message('Please wait, you will be connected with '+name.firstChild.name.strip()+' through an audio call.')
			audioCall.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Video call'),
		gesture= 'kb:control+shift+v'
	)
	def script_videoCall(self, gesture):
		name = self.get('TitleButton', False, None)
		videoCall = self.get('VideoCallButton', True, gesture)
		if videoCall:
			message('Please wait, you will be connected with '+name.firstChild.name.strip()+' through a video call.')
			videoCall.doAction()
		else:
			message(self.notFound)

	@script(
		category= 'WhatsAppEnhancements',
		# Item Description in Input Gestures Dialog
		description= _('Activate and deactivate the reading of phone numbers for unsaved contacts while reading messages'),
		gesture= 'kb:control+shift+n'
	)
	def script_viewConfigToggle(self, gesture):
		self.configFile()
		with open(f'{appArgs.configPath}\\WhatsAppEnhancements.ini', 'w') as f:
			if self.viewConfig == 'enabled':
				f.write('disabled')
				self.viewConfig = 'disabled'
				message(_('Reading phone number disabled'))
			else:
				f.write('enabled')
				self.viewConfig = 'enabled'
				message(_('Reading phone number enabled'))
