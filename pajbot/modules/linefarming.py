import logging

from pajbot.modules import BaseModule, ModuleSetting
from pajbot.models.command import Command

log = logging.getLogger(__name__)

class LineFarmingModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Line Farming'
    DESCRIPTION = 'Keep track on the amount of lines users type in chat'
    ENABLED_DEFAULT = True
    SETTINGS = [
            ModuleSetting(
                key='count_offline',
                label='Count lines in offline chat',
                type='boolean',
                required=True,
                default=False)
                ]

    def __init__(self):
        super().__init__()
        self.bot = None

    def on_pubmsg(self, source, message):
        if self.bot.is_online:
            source.num_lines += 1
        elif self.settings['count_offline'] is True:
            source.num_lines += 1

    def enable(self, bot):
        if bot:
            bot.add_handler('on_pubmsg', self.on_pubmsg)
            self.bot = bot

    def disable(self, bot):
        if bot:
            bot.remove_handler('on_pubmsg', self.on_pubmsg)
