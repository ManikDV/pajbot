import logging
import re

from pajbot.modules import BaseModule, ModuleSetting
from pajbot.models.command import Command
from pajbot.models.handler import HandlerManager

log = logging.getLogger(__name__)

class EmotesOnScreenModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Emotes on Screen (CLR)'
    DESCRIPTION = 'Shows one emote on screen per message'
    SETTINGS = [
            ModuleSetting(
                key='valid_emotes',
                label='Valid emotes (separate by spaces). Leave empty for all emotes',
                type='text',
                required=True,
                placeholder='i.e. Kappa Keepo PogChamp KKona',
                default='')
                ]

    def on_message(self, source, message, emotes, whisper, urls):
        if len(emotes) > 0:
            if len(self.settings['valid_emotes']) > 1 and emotes[0]['code'] not in self.settings['valid_emotes']:
                # If the first emote isn't a valid emote, don't show it on screen.
                return

            self.bot.websocket_manager.emit('new_emote', {'emote': emotes[0]})

    def enable(self, bot):
        self.bot = bot
        HandlerManager.add_handler('on_message', self.on_message)

    def disable(self, bot):
        HandlerManager.remove_handler('on_message', self.on_message)
