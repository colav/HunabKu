# import subprocess
import requests
import sys
import os
from shutil import rmtree
from command import run, CommandException

from hunabku.Hunabku import Hunabku
from hunabku.Config import ConfigGenerator

import unittest


class TestHunabku(unittest.TestCase):
    """
    Class to tests hunabku server options
    """
    def setUp(self):
        print('running setUp')
        # Inicializa la aplicación Flask
        self.config_gen = ConfigGenerator()
        self.config = self.config_gen.config
        self.server = Hunabku(self.config)

    def test__loads(self):
        self.server.apidoc_setup()
        self.server.load_plugins()
        self.server.generate_doc()
        rmtree("hunabku_website", ignore_errors=True)

    def test__generate_config(self):
        print('############################ running generated config ############################')
        res = run(['hunabku_server', '--generate_config', 'config.py'])

        print(res.output)
        if res.exit != 0:
            print("ERROR: generating config")
            sys.exit(res.exit)
        res = run(['hunabku_server', '--generate_config',
                  'config.py', '--overwrite'])
        if res.exit != 0:
            print("ERROR: generating config overwriting")
            sys.exit(res.exit)

    def test__generated_plugin(self):
        print('############################ running generaying plugin tests ############################')
        res = run(['hunabku_server', '--generate_plugin', 'test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)
        res = run(['pip', 'install', './HunabKu_test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)

        del self.server
        self.server = Hunabku(self.config)
        self.server.apidoc_setup()
        self.server.load_plugins()
        self.server.generate_doc()

        print(res.output.decode())

    def test__duplicated_endpoint(self):
        print('############################ running duplicate endpoint tests ############################')
        res = run(['hunabku_server', '--generate_plugin', 'test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)
        res = run(['pip', 'install', './HunabKu_test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)

        res = run(['hunabku_server', '--generate_plugin', 'test2'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)
        res = run(['pip', 'install', './HunabKu_test2'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)
        try:
            res = run(['hunabku_server'])
        except CommandException as e:
            print(e.output)
            if e.exit  != 0:
                print("INFO: loading multiple times the same endpoint fails, TEST PASSED")
            else:
                print("INFO: loading multiple times the same endpoint not fail, TEST FAILED")
                sys.exit(1)



    def tearDown(self):
        print('############################ running tearDown ############################')
        rmtree("HunabKu_test", ignore_errors=True)
        rmtree("HunabKu_test2", ignore_errors=True)
        if os.path.exists("config.py"):
            os.remove("config.py")

        res = run(['pip', 'uninstall', '-y', 'hunabku_test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: uninstalling test plugin")

        res = run(['pip', 'uninstall', '-y', 'hunabku_test2'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: uninstalling test plugin")

if __name__ == '__main__':
    unittest.main()
