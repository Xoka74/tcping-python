import socket
import time
from dataclasses import dataclass
from timeit import default_timer as timer

import click
from click import option, echo, argument, Choice, command


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    count: float
    timeout: int
    interval: int
    ip_version: str
    constant_ping: bool


@dataclass
class PingResult:
    time: float
    is_successful: bool


class Socket:
    def __init__(self, config: Config):
        self._config = config
        self.ip_type = socket.AF_INET if self._config.ip_version == 'IPv4' else socket.AF_INET6
        self._socket = socket.socket(self.ip_type, socket.SOCK_STREAM)
        self._socket.settimeout(self._config.timeout)

    def connect(self):
        if self.ip_type == socket.AF_INET:
            self._socket.connect((self._config.host, self._config.port))
        else:
            self._socket.connect((self._config.host, self._config.port, 0, 0))


class Logger:
    def __init__(self, config: Config):
        self._config = config

    def log_start(self):
        start = click.style('[START]', fg='blue')
        count = 'Constantly' if self._config.constant_ping else self._config.count

        echo(f'{start} {count}'
             f' Pings to {self._config.host}[:{self._config.port}]')

    def log_result(self, result: PingResult):
        if result.is_successful:
            connected = click.style('[CONNECTED]', fg='green')
            echo(f'{connected} {self._config.host}[:{self._config.port}]'
                 f' time={result.time:0.2f} ms')
        else:
            timeout = click.style('[TIMEOUT]', fg='red')
            echo(f'{timeout} {self._config.host}[:{self._config.port}]')

    def log_error(self, message):
        error = click.style('[ERROR]', fg='red')
        echo(f'{error} {message}')

    @staticmethod
    def log_shutdown():
        echo(click.style('[SHUTDOWN]', fg='blue'))


class Ping:
    def __init__(self, config):
        self._config = config
        self._logger = Logger(config)
        self._results = []

    def ping(self):
        self._logger.log_start()
        try:
            self._ping()
        except KeyboardInterrupt:
            pass
        except:
            self._logger.log_error('Unexpected error')

        self._logger.log_shutdown()

    def _ping(self):
        i = 0
        while i < self._config.count or self._config.constant_ping:
            sock = Socket(self._config)
            try:
                start = timer()
                sock.connect()
                estimated = (timer() - start) * 1000
                result = PingResult(estimated, True)
            except socket.timeout:
                result = PingResult(0, False)
            except socket.gaierror:
                return self._logger.log_error('Unable to resolve host')

            self._results.append(result)
            self._logger.log_result(result)
            time.sleep(self._config.interval)
            i += 1


@argument('host')
@option('-p', '--port', default=80, help='Port to connect')
@option('-cp', '--constant-ping', default=False, is_flag=True)
@option('-c', '--count', default=1, type=click.IntRange(0),
        help='Amount of pings')
@option('-t', '--timeout', default=1, type=click.IntRange(0),
        help='Connection timeout in seconds')
@option('-i', '--interval', default=1, type=click.IntRange(0),
        help='Interval between requests in seconds')
@option('--ip-version', default='IPv4', type=Choice(['IPv4', 'IPv6']))
@command(context_settings=dict(help_option_names=['-h', '--help']))
def ping(**kwargs):
    config = Config(**kwargs)
    Ping(config).ping()


if __name__ == '__main__':
    ping()
