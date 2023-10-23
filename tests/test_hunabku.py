# import subprocess
import requests
import sys
import os
import time
import signal
from shutil import rmtree
import subprocess
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
            if e.exit != 0:
                print(
                    "INFO: loading multiple times the same endpoint fails, TEST PASSED")
            else:
                print(
                    "INFO: loading multiple times the same endpoint not fail, TEST FAILED")
                sys.exit(1)

    def test__apidoc_endpoint(self):
        print('############################ running apidoc service tests ############################')
        res = run(['hunabku_server', '--generate_plugin', 'apidoc'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)
        res = run(['pip', 'install', './HunabKu_apidoc'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: generating config plugin")
            sys.exit(res.exit)

        process = subprocess.Popen(
            "hunabku_server", shell=False, preexec_fn=os.setsid)
        if process.returncode is not None:
            print("ERROR: running hunabku server")
            sys.exit(process.returncode)
        time.sleep(10)
        req = requests.get("http://0.0.0.0:8080/apidoc/index.html")
        if req.status_code != 200:
            print("ERROR: testing apidoc service")
            process.send_signal(signal.SIGINT)
            process.wait()
            if process.returncode != 0:
                print("ERROR: killing hunabku server")
            sys.exit(process.returncode)
        process.send_signal(signal.SIGINT)
        process.wait()
        if process.returncode != 0:
            print("ERROR: killing hunabku server")
            sys.exit(process.returncode)

    def tearDown(self):
        print('############################ running tearDown ############################')
        rmtree("HunabKu_test", ignore_errors=True)
        rmtree("HunabKu_test2", ignore_errors=True)
        rmtree("HunabKu_apidoc", ignore_errors=True)
        if os.path.exists("config.py"):
            os.remove("config.py")

        res = run(['pip', 'uninstall', '-y', 'hunabku_test'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: uninstalling test plugin")

        res = run(['pip', 'uninstall', '-y', 'hunabku_test2'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: uninstalling test2 plugin")

        res = run(['pip', 'uninstall', '-y', 'hunabku_apidoc'])
        print(res.output.decode())
        if res.exit != 0:
            print("ERROR: uninstalling apidoc plugin")


if __name__ == '__main__':
    unittest.main()
