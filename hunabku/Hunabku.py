from flask import (
    Flask
)

import logging

import os
from hunabku.HunabkuBase import HunabkuPluginBase
from hunabku.Config import ConfigGenerator, Config
from hunabku._version import get_version
from shutil import rmtree
from distutils.dir_util import copy_tree
import subprocess
import inspect
import glob
import time
import pathlib
import sys
import importlib
import json

import pkgutil


class Hunabku:
    """
    Hunabku class is the main class to start the server,
    it allows to load plugins, generate documentation and start the server.
    The server can be started with the following command:
    hunabku_server --config config.py

    by default the server will start in http://0.0.0.0:8080

    """
    config = ConfigGenerator.config

    def __init__(self, config: Config):
        """
        Contructor to initialize configuration options.

        Args:
            apikey: apikey to access the data
            ip (str): ip to start the server
            port (int): port for the server
            info_level (logging.DEBUG/INFO etc..): enable/disable debug mode with extra messages output.
        """
        self.config.update(config)
        self.plugin_prefix = "hunabku"
        self.apidoc_dir = self.config.apidoc.apidoc_dir
        self.apidoc_static_dir = self.apidoc_dir + '/static'
        self.apidoc_output_dir = self.apidoc_dir + '/static/apidoc'
        self.apidoc_templates_dir = self.apidoc_dir + '/templates'
        self.apidoc_config_dir = self.apidoc_dir + '/config'
        self.apidoc_config_data = {}
        if self.config.apidoc.use_https:
            protocol = 'https'
        else:
            protocol = 'http'
        if self.config.apidoc.show_port:
            port = ':' + str(self.config.port)
        else:
            port = ''
        self.apidoc_config_data['url'] = f'{protocol}://' + \
            config.host + port
        self.apidoc_config_data['sampleUrl'] = f'{protocol}://' + \
            config.host + port

        self.apidoc_config_data['header'] = {}
        self.apidoc_config_data['header']['filename'] = self.apidoc_config_dir + \
            '/apidoc-header.md'
        self.apidoc_config_data['version'] = get_version()
        self.pkg_config_dir = str(
            pathlib.Path(__file__).parent.absolute()) + '/config/'
        self.pkg_templates_dir = str(
            pathlib.Path(__file__).parent.absolute()) + '/templates/'
        self.plugins = []
        self.logger = logging.getLogger(__name__)
        self.set_info_level(config["info_level"])
        self.app = Flask(
            "Hunabku",
            static_folder=self.apidoc_static_dir,
            static_url_path='/',
            template_folder=self.apidoc_templates_dir)

    def apidoc_setup(self):
        """
        creates an ApiDoc folder to dump configuration and documentation of the APIs
        """
        try:
            os.makedirs(self.apidoc_dir, exist_ok=True)
            print(" * ApidDoc Directory ", self.apidoc_dir, " created ")
        except FileExistsError:
            # Is this is happening then restart the microservices in the folder
            print(
                " * Warning! ApidDoc Directory ",
                self.apidoc_dir,
                " already exists")

        try:
            os.mkdir(self.apidoc_static_dir)
            print(
                " * ApiDoc Static Directory ",
                self.apidoc_static_dir,
                " created ")
        except FileExistsError:
            # Is this is happening then restart the microservices in the folder
            print(
                " * Warning! ApiDoc Static Directory ",
                self.apidoc_static_dir,
                " already exists")

        try:
            os.mkdir(self.apidoc_output_dir)
            print(" * ApiDoc Static Output Directory ",
                  self.apidoc_output_dir, " created ")
        except FileExistsError:
            # Is this is happening then restart the microservices in the folder
            print(
                " * Warning! ApiDoc Static Output Directory ",
                self.apidoc_output_dir,
                " already exists")

        try:
            os.mkdir(self.apidoc_templates_dir)
            print(
                " * ApiDoc Templates Directory ",
                self.apidoc_templates_dir,
                " created ")
        except FileExistsError:
            # Is this is happening then restart the microservices in the folder
            print(
                " * Warning! ApiDoc Templates Directory ",
                self.apidoc_templates_dir,
                " already exists")

        try:
            os.mkdir(self.apidoc_config_dir)
            print(
                " * ApiDoc Config Directory ",
                self.apidoc_static_dir,
                " created ")
        except FileExistsError:
            # Is this is happening then restart the microservices in the folder
            print(
                " * Warning! ApiDoc Static Directory ",
                self.apidoc_static_dir,
                " already exists")

        copy_tree(self.pkg_config_dir, self.apidoc_config_dir)
        apidoc_config_data = {}
        with open(self.apidoc_config_dir + '/apidoc.json') as json_file:
            apidoc_config_data = json.load(json_file)

        apidoc_config_data.update(self.apidoc_config_data)
        with open(self.apidoc_config_dir + '/apidoc.json', 'w') as json_file:
            json.dump(apidoc_config_data, json_file)

        copy_tree(self.pkg_templates_dir, self.apidoc_templates_dir)

    def set_info_level(self, info_level):
        """
        Information level for debug or verbosity of the application (https://docs.python.org/3.1/library/logging.html)
        """
        if info_level != logging.DEBUG:
            logging.basicConfig(
                filename=self.config["log_file"], level=info_level)
        self.config["info_level"] = info_level

    def load_plugins(self, verbose=True):
        """
        This method return the plugins found in the folder plugins.
        """
        if verbose:
            self.logger.warning('-----------------------')
            self.logger.warning('------ Loading Plugins:')
        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name.startswith(self.plugin_prefix + '_')
        }
        for discovered_plugin in discovered_plugins:
            for path in glob.glob(
                    str(discovered_plugins[discovered_plugin].__path__[0]) + "/endpoints/*.py"):
                mname = path.split(os.path.sep)[-1].replace('.py', '')
                if verbose:
                    self.logger.warning(
                        f'------ Loading plugin module from package {discovered_plugin} and module {mname}.py :')
                spec = importlib.util.spec_from_file_location(mname, path)
                module = spec.loader.load_module()
                for cname, plugin_class in inspect.getmembers(module):
                    if inspect.isclass(plugin_class) and issubclass(plugin_class, HunabkuPluginBase) and plugin_class is not HunabkuPluginBase: # noqa  E501
                        if verbose:
                            self.logger.warning(
                                f'------ Registering plugin class: {mname}.{cname}')

                        current_config = {}
                        if discovered_plugin in self.config.keys():
                            if mname in self.config[discovered_plugin].keys():
                                if cname in self.config[discovered_plugin][mname].keys():
                                    current_config = self.config[discovered_plugin][mname][cname]
                        plugin_class.config.update(current_config)
                        instance = plugin_class(self)
                        instance.config.update(current_config)
                        instance.register_endpoints()
                        plugin = {}
                        plugin['package'] = discovered_plugin
                        plugin['mod_name'] = mname
                        plugin['class'] = plugin_class
                        plugin['class_name'] = cname
                        plugin['name'] = f"{discovered_plugin}.{mname}.{cname}"
                        plugin['path'] = path
                        plugin['spec'] = spec
                        plugin['instance'] = instance
                        self.plugins.append(plugin)
                        if verbose:
                            self.logger.warning(
                                f'------ Registered plugin class: {mname}.{cname}  DONE')

    def check_apidoc_syntax(self, plugin_file):
        """
        Allows to check in the syntaxis in the docstring comment is right
        for apidoc  files generation.
        The the syntax is wrong, the Hunabku server can not start.

        Parameters:
        ___________
        plugin_file: str
            path to the plugin file to check (python file)
        """
        args = ['apidoc', '-c', self.apidoc_config_dir + os.path.sep + "apidoc.json", '-i',
                str(pathlib.Path(plugin_file).parent.absolute()),
                '--dry-run',
                '-f',
                plugin_file]
        process = subprocess.run(args,
                                 stdout=subprocess.PIPE)
        if process.returncode != 0:
            self.logger.error(
                '------ERROR: parsing docstring for apidocs in plugin ' + plugin_file)
            self.logger.error(
                '             server can not start until apidocs syntax is fixed')
            self.logger.error(process)
            sys.exit(1)

    def generate_doc(self, timeout=1, maxtries=5):
        """
        This method allows to generated apidocs documentation parsing plugin files.

        Parameters:
        ___________
        timeout: int
            timeout in seconds to wait for the process to finish
        maxtries: int
            max number of tries to wait for the process to finish
        """
        self.logger.warning('-----------------------')
        self.logger.warning('------ Creating documentation')

        rmtree(self.apidoc_static_dir, ignore_errors=True)
        args = ['apidoc', '-c',
                self.apidoc_config_dir + os.path.sep + "apidoc.json"]

        for plugin in self.plugins:
            self.check_apidoc_syntax(plugin['path'])
            args.append('-i')
            args.append(str(pathlib.Path(plugin['path']).parent.absolute()))
            args.append('-f')
            args.append(plugin['path'])
        args.append('-o')
        args.append(self.apidoc_output_dir)
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        counter = 0
        while process.poll() is None:
            time.sleep(timeout)
            counter = counter + 1
            if counter == maxtries:
                process.kill()
                break
        self.logger.warning(
            '------ Apidocs at http://{}:{}/apidoc/index.html'.format(self.config.host, self.config.port))

    def start(self):
        """
        Method to start server
        """
        self.app.run(host=self.config.host, port=self.config.port,
                     debug=True, use_reloader=self.config.use_reloader)
