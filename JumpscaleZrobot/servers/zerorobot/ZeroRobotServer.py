import logging

from jumpscale import j
from Jumpscale.logging.Handlers import TelegramFormatter, TelegramHandler
from zerorobot.robot import Robot

telegram_logger = logging.getLogger('telegram_logger')
telegram_logger.disabled = True


TEMPLATE = """
listen = ":6600"
data_repo = ""
template_repo  = [""]
config_repo = ""
config_key = ""
debug = false
telegram_bot_token = ""
telegram_chat_id = ""
auto_push = false
auto_push_interval = 10
organization = ""
block = true
"""
JSConfigBase = j.tools.configmanager.base_class_config


class ZeroRobotServer(JSConfigBase):

    def __init__(self, instance, data={}, parent=None, interactive=False, template=TEMPLATE):
        JSConfigBase.__init__(self, instance=instance, data=data, parent=parent, template=template, interactive=interactive)
        self._robot = None

    @property
    def address(self):
        if self._robot:
            return self._robot.address

    def start(self):
        """
        start the 0-robot daemon.
        this will start the REST API on address and port specified by --listen and block

        Arguments:
            listen {string} -- listen address (default :6600)
            data_repo {string} -- URL of the git repository or absolute path where to save the data of the zero robot
            template_repo {list} -- list of template repository URL. Use fragment URL to specify a branch: http://github.com/account/repo#branch'
            config_repo {string} -- URL of the configuration repository (https://github.com/Jumpscale/core9/blob/development/docs/config/configmanager.md)
            config_key {string} -- Absolute path to ssh key to secure configuration data, which is committed and pushed (see auto-push) in the configuration repo
            debug {boolean} -- enable debug logging
            telegram_bot_token {string} -- Bot to push template action failures
            telegram_chat_id {string} -- Chat id to push template action failures
            auto_push {boolean} -- enable automatically commit and pushing of data repository
            auto_push_interval {integer} -- interval in minutes of automatic pushing of data repository
            organization {string} -- if specified, enable JWT authentication for each request

        Raises:
            ValueError -- when telegram_bot is enable but no chat id is specified
        """
        data_repo = self.config.data['data_repo']
        listen = self.config.data.get('listen', ':6600')
        template_repo = self.config.data.get('template_repo')
        config_repo = self.config.data.get('config_repo') or None
        config_key = self.config.data.get('config_key') or None
        debug = self.config.data.get('debug', False)
        telegram_bot_token = self.config.data.get('telegram_bot_token') or None
        telegram_chat_id = self.config.data.get('telegram_chat_id') or None
        auto_push = self.config.data.get('auto_push', False)
        auto_push_interval = self.config.data.get('auto_push_interval', False)
        organization = self.config.data.get('organization') or None
        block = self.config.data.get('block', True)

        level = "INFO"
        if debug:
            level = "DEBUG"

        j.logger.handlers_level_set(level)
        j.logger.loggers_level_set(level)

        if (telegram_bot_token and not telegram_chat_id) or (telegram_chat_id and not telegram_bot_token):
            raise ValueError("To enable telegram error logging, you need to specify both the --telegram-bot-token and the --telegram-chat-id options")

        if telegram_bot_token:
            telegram_logger.disabled = False
            telegrambot = j.clients.telegram_bot.get(instance='errorbot', data=dict(bot_token_=telegram_bot_token))
            handler = TelegramHandler(telegrambot, telegram_chat_id)
            handler.setFormatter(TelegramFormatter())
            handler.setLevel(logging.ERROR)
            telegram_logger.addHandler(handler)

        self._robot = Robot()

        for url in template_repo or []:
            self._robot.add_template_repo(url)

        self._robot.set_data_repo(data_repo)
        self._robot.set_config_repo(config_repo, config_key)

        self._robot.start(listen=listen, auto_push=auto_push, auto_push_interval=auto_push_interval,
                          jwt_organization=organization, block=block)

    def stop(self, timeout=30):
        if self._robot:
            self._robot.stop(timeout=timeout)
            self._robot = None
