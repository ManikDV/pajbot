import logging
import random

from pajbot.modules import BaseModule, ModuleSetting
from pajbot.models.command import Command
from pajbot.models.handler import HandlerManager
from pajbot.managers import RedisManager
from pajbot.tbutil import find
from pajbot.streamhelper import StreamHelper

log = logging.getLogger(__name__)

class QuestModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Quest system'
    DESCRIPTION = 'Give users a single quest at the start of each day'
    SETTINGS = []

    def __init__(self):
        super().__init__()
        self.current_quest = None

    def my_progress(self, **options):
        bot = options['bot']
        source = options['source']
        if self.current_quest is not None:
            quest_progress = source.get_quest_progress()
            if quest_progress is not False:
                bot.say('Your current quest progress is {}'.format(quest_progress))
            else:
                bot.say('You have no progress on the current quest.')
        else:
            bot.say('There is no quest active right now.')

    def get_current_quest(self, **options):
        bot = options['bot']
        if self.current_quest is not None:
            bot.say('Current quest active: {0.NAME} - {0.OBJECTIVE}'.format(self.current_quest))
        else:
            bot.say('There is no quest active right now.')

    def get_user_tokens(self, **options):
        bot = options['bot']
        source = options['source']

        bot.say('{} has {} tokens'.format(source.username_raw, source.get_tokens()))

    def load_commands(self, **options):
        self.commands['myprogress'] = Command.raw_command(self.my_progress)
        self.commands['currentquest'] = Command.raw_command(self.get_current_quest)
        self.commands['tokens'] = Command.raw_command(self.get_user_tokens)

    def on_stream_start(self):
        available_quests = list(filter(lambda m: m.ID.startswith('quest-'), self.submodules))
        if len(available_quests) == 0:
            log.error('No quests enabled.')
            return False

        self.current_quest = random.choice(available_quests)
        self.current_quest.start_quest()

        redis = RedisManager.get()

        redis.set(self.current_quest_key, self.current_quest.ID)

        self.bot.say('Stream started, new quest has been chosen!')
        self.bot.say('Current quest objective: {}'.format(self.current_quest.OBJECTIVE))

    def on_stream_stop(self):
        if self.current_quest is None:
            log.info('No quest active on stream stop.')
            return False

        self.current_quest.stop_quest()
        self.current_quest = None
        self.bot.say('Stream ended, quest has been reset.')

        redis = RedisManager.get()

        # Remove any mentions of the current quest
        redis.delete(self.current_quest_key)

        last_stream_id = StreamHelper.get_last_stream_id()
        if last_stream_id is False:
            log.error('No last stream ID found.')
            # No last stream ID found. why?
            return False

        # XXX: Should we use a pipeline for any of this?
        # Go through user tokens and remove any from more than 2 streams ago
        for key in redis.keys('{streamer}:*:tokens'.format(streamer=StreamHelper.get_streamer())):
            all_tokens = redis.hgetall(key)
            for stream_id_str in all_tokens:
                try:
                    stream_id = int(stream_id_str)
                except (TypeError, ValueError):
                    log.error('Invalid stream id in tokens by {}'.format(key))
                    continue

                if last_stream_id - stream_id > 1:
                    log.info('Removing tokens for stream {}'.format(stream_id))
                    redis.hdel(key, stream_id)

    def enable(self, bot):
        HandlerManager.add_handler('on_stream_start', self.on_stream_start)
        HandlerManager.add_handler('on_stream_stop', self.on_stream_stop)

        self.bot = bot

    def on_loaded(self):
        if self.bot:
            self.current_quest_key = '{streamer}:current_quest'.format(streamer=self.bot.streamer)

            if self.current_quest is None:
                redis = RedisManager.get()

                current_quest_id = redis.get(self.current_quest_key)

                log.info('Try to load submodule with ID {}'.format(current_quest_id))

                if current_quest_id is not None:
                    current_quest_id = current_quest_id.decode('utf8')
                    quest = find(lambda m: m.ID == current_quest_id, self.submodules)

                    if quest is not None:
                        log.info('Resumed quest {}'.format(quest.OBJECTIVE))
                        self.current_quest = quest
                        self.current_quest.start_quest()
                    else:
                        log.info('No quest with id {} found in submodules ({})'.format(current_quest_id, self.submodules))
                else:
                    # Fake a stream start to try to randomize a quest
                    self.on_stream_start()

    def disable(self, bot):
        HandlerManager.remove_handler('on_stream_start', self.on_stream_start)
        HandlerManager.remove_handler('on_stream_stop', self.on_stream_stop)
