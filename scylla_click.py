from dataclasses import dataclass
from typing import Union

import click
import requests
from click import Command, Option, Argument

URL_SCHEMA = "http://"
DEFAULT_ROOT = "localhost:10000/"


@dataclass
class Colors:
    bright_blue: str = r"bright_blue"
    magenta: str = r"magenta"
    blue: str = r"blue"
    red: str = r"red"


@click.group()
@click.option("-a", "--address", help="IP address of server node", default="localhost", show_default=True)
@click.option("-p", "--port", help="Api port", default="10000", show_default=True)
def scylla_cli(address: str, port: str):
    global DEFAULT_ROOT
    DEFAULT_ROOT = f"{address}:{port}/"


class MockSwaggerObj:
    def __init__(self,
                 root: str,
                 path: str = "",
                 params: list[Union[Option, Argument]] = None,
                 help: str = None):
        self.root = root
        self.path = path
        self.params = params
        self.help = help
        self.name = f"{self.root}-{self.path.strip('/')}".replace("/", "-")
        self.url_path = self.root + f"{self.path}" if self.path else self.root

    def __repr__(self):
        return f"* {self.name} URL: {self.url_path} Help: {self.help}"

    @property
    def callback(self):
        def clbck():
            click.echo(f"{click.style('Calling: ', fg=Colors.bright_blue)}"
                       f"{click.style(self.name, fg='magenta')}")
        return clbck


class MockUptimeMs(MockSwaggerObj):
    def __init__(self,
                 root: str = "system",
                 path: str = "/uptime_ms",
                 params: list[Option] = None,
                 help: str = "Get system uptime, in milliseconds"):
        super().__init__(root, path, params, help)

    @property
    def callback(self):
        def clbck():
            url = f"{URL_SCHEMA}{DEFAULT_ROOT}{self.url_path}"
            click.secho(f"Sending request to: {url}")
            response = requests.get(url=url)
            status = 0 if response.ok else 1
            color = Colors.blue if response.ok else Colors.red
            click.secho(f"Status: {str(status)}", fg=color)
            click.secho(f"API response: {response.text}", fg=Colors.blue)

        return clbck


Config = MockSwaggerObj(root="config",
                        params=[Option(param_decls=["--id"],
                                       help="ID of config to return",
                                       required=True)],
                        help="Return a config value")
GossiperDown = MockSwaggerObj(root="gossiper",
                              path="/endpoint/down/",
                              help="Get the addresses of the down endpoints")
GossiperLive = MockSwaggerObj(root="gossiper",
                              path="/endpoint/live/",
                              help="Get the addreses of live endpoints")
SystemUptimeMs = MockUptimeMs()


def get_swagger_objs():
    return [Config, GossiperDown, GossiperLive, SystemUptimeMs]


def command_factory():
    click.secho("Loading swagger objects...", fg=Colors.magenta)
    cmds = get_swagger_objs()  # this would be provided by the swagger integration

    group_names = set([cmd.root for cmd in cmds])
    groups = []

    for group_name in group_names:
        new_group = click.Group(name=group_name)
        groups.append(new_group)
        scylla_cli.add_command(new_group)

    with click.progressbar(cmds) as cmd_list:
        for cmd in cmd_list:
            group = [group for group in groups if group.name in cmd.root][0]
            group.add_command(Command(name=f"{cmd.root}{cmd.path}".replace("/", "-").strip("-"),
                                           callback=cmd.callback,
                                           params=cmd.params,
                                           help=cmd.help))
    click.secho("Done.", fg=Colors.magenta)


command_factory()
