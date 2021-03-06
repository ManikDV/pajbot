import logging
import datetime

from pajbot.modules import BaseModule, ModuleSetting
from pajbot.models.command import Command, CommandExample
from pajbot.models.handler import HandlerManager

from numpy import random

log = logging.getLogger(__name__)

class RaffleModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Raffle (mini game)'
    DESCRIPTION = 'Enables raffles for points'
    SETTINGS = [
            ModuleSetting(
                key='max_points',
                label='Max points for a single raffle',
                type='number',
                required=True,
                placeholder='',
                default=3000,
                constraints={
                    'min_value': 0,
                    'max_value': 35000,
                    }),
                ]

    def __init__(self):
        super().__init__()

        self.raffle_running = False
        self.raffle_users = []
        self.raffle_points = 0

    def load_commands(self, **options):
        self.commands['raffle'] = Command.raw_command(self.raffle,
                delay_all=0,
                delay_user=0,
                level=500,
                description='Start a raffle for points',
                examples=[
                    CommandExample(None, 'Start a raffle for 69 points',
                        chat='user:!raffle 69\n'
                        'bot:A raffle has begun for 69 points. Type !join to join the raffle! The raffle will end in in 60 seconds.',
                        description='Start a 60-second raffle for 69 points').parse(),
                    CommandExample(None, 'Start a raffle for the default value of {} points',
                        chat='user:!raffle 69 30\n'
                        'bot:A raffle has begun for 69 points. Type !join to join the raffle! The raffle will end in in 30 seconds.',
                        description='Start a 30-second raffle for 69 points').parse(),
                    ],
                )
        self.commands['join'] = Command.raw_command(self.join,
                delay_all=0,
                delay_user=5,
                description='Join a running raffle',
                examples=[
                    CommandExample(None, 'Join a running raffle',
                        chat='user:!join',
                        description='You don\'t get confirmation whether you joined the raffle or not.').parse(),
                    ],
                )

    def raffle(self, **options):
        """ Starts a raffle.
        TODO: Read the second argument and try to use that as the amount of time the raffle is running for.
        """

        bot = options['bot']
        source = options['source']
        message = options['message']

        if self.raffle_running is True:
            bot.say('{0}, a raffle is already running OMGScoots'.format(source.username_raw))
            return False

        self.raffle_users = []
        self.raffle_running = True
        self.raffle_points = 100

        try:
            if message is not None:
                self.raffle_points = int(message.split()[0])
        except ValueError:
            pass

        self.raffle_points = min(self.raffle_points, self.settings['max_points'])

        bot.websocket_manager.emit('notification', {'message': 'A raffle has been started!'})
        bot.execute_delayed(0.75, bot.websocket_manager.emit, ('notification', {'message': 'Type !join to enter!'}))

        bot.me('A raffle has begun for {} points. type !join to join the raffle! The raffle will end in 60 seconds'.format(self.raffle_points))
        bot.execute_delayed(15, bot.me, ('The raffle for {} points ends in 45 seconds! Type !join to join the raffle!'.format(self.raffle_points), ))
        bot.execute_delayed(30, bot.me, ('The raffle for {} points ends in 30 seconds! Type !join to join the raffle!'.format(self.raffle_points), ))
        bot.execute_delayed(45, bot.me, ('The raffle for {} points ends in 15 seconds! Type !join to join the raffle!'.format(self.raffle_points), ))

        bot.execute_delayed(60, self.end_raffle)

    def join(self, **options):
        source = options['source']
        if not self.raffle_running:
            return False

        for user in self.raffle_users:
            if user == source:
                return False

        # Added user to the raffle
        self.raffle_users.append(source)

    def end_raffle(self):
        if not self.raffle_running:
            return False

        self.raffle_running = False

        if len(self.raffle_users) == 0:
            self.bot.me('Wow, no one joined the raffle DansGame')
            return False

        winner = random.choice(self.raffle_users)

        self.raffle_users = []

        self.bot.websocket_manager.emit('notification', {'message': '{} won {} points in the raffle!'.format(winner.username_raw, self.raffle_points)})
        self.bot.me('The raffle has finished! {0} won {1} points! PogChamp'.format(winner.username_raw, self.raffle_points))

        winner.points += self.raffle_points

        HandlerManager.trigger('on_raffle_win', winner, self.raffle_points)

    def enable(self, bot):
        self.bot = bot
