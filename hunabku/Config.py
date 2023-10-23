
import sys
import os
import logging


class Config:
    """
    Config class provides a way to create and manage a configuration object in Python.
    This class uses the __setattr__, __getattr__, keys, __getitem__, __setitem__, get,
    and update methods to enable easy access and modification of configuration values.

    Overall, the Config class provides a convenient way to manage configuration values
    in Python with an easy-to-use API.
    """

    def __init__(self):
        self.__docs__ = {}
        self.__fromparam__ = False
        if "__docs__" in self.__docs__:
            del self.__docs__["__docs__"]
        if "__fromparam__" in self.__docs__:
            del self.__docs__["__fromparam__"]

    def __setattr__(self, key: str, value: any):
        """
        Set the attribute `value` to the given `key` in the `__dict__` dictionary of the `Config` object.

        Parameters
        ----------
        key : str
            The key of the attribute.
        value : Any
            The value to be set to the attribute.

        Returns
        -------
        None
        """
        self.__dict__[key] = value

    def __getattr__(self, key: str):
        """
        Retrieve the attribute value for the given `key` from the `__dict__` dictionary of the `Config` object.

        Parameters
        ----------
        key : str
            The key of the attribute.

        Returns
        -------
        Any
            The value of the attribute with the given `key`.
        """
        value = self.__dict__.get(key, None)
        if value is not None:
            return value
        else:
            self.__dict__[key] = Config()
            return self.__dict__[key]

    def keys(self):
        _keys = list(self.__dict__.keys())
        _keys.remove("__docs__")
        _keys.remove("__fromparam__")
        return _keys

    def __getitem__(self, key: str):
        return self.__dict__[key]

    def __setitem__(self, key: str, value: any):
        self.__dict__[key] = value

    def get(self, key: str) -> any:
        return self.__dict__.get(key, None)

    def _update(self, preconfig, config):
        for key in config.keys():
            if isinstance(config[key], Config):
                if key not in preconfig.keys():
                    preconfig[key] = config[key]
                preconfig[key] = self._update(preconfig[key], config[key])
            else:
                preconfig[key] = config[key]
                if key in config.__docs__:
                    preconfig.__docs__ = config.__docs__[key]
        return preconfig

    def update(self, config):
        self = self._update(self, config)

    def __iadd__(self, other):
        name = list(other.keys())[0]
        value = other[name]
        if name in other.__docs__:
            doc = other.__docs__[name]
            self.__docs__[name] = doc
        self[name] = value
        self.__fromparam__ = False
        if "__fromparam__" in self.__docs__:
            del self.__docs__["__fromparam__"]
        return self

    def fromparam(self):
        return self.__fromparam__

    def doc(self, doc):
        """
        Used when Param(db="Colav").doc("MongoDB database name") is called,
        Param only has one key.
        """
        if self.fromparam():
            name = list(self.keys())[0]
            self.__docs__[name] = doc
            return self
        else:
            print("ERROR: this method only can be call from class Param",
                  file=sys.stderr)
            sys.exit(1)

    def set_doc(self, var: str, doc: str):
        self.__docs__[var] = doc

    def _dict(self, config, root=True) -> dict:
        """
        This method creates a dictionary from the config object
        """
        info = {}
        if root:
            cnf = Config()
            cnf.config = config
            config = cnf

        for key in config.keys():
            if isinstance(config[key], Config):
                info[key] = self._dict(config[key], False)
            else:
                value = config[key]
                doc = ""
                if key in config.__docs__:
                    doc = config.__docs__[key]
                info[key] = {'value': value, 'doc': doc}

        return info

    def dict(self):
        return self._dict(self)


class Param:
    def __new__(cls, **kwargs):
        if len(kwargs) == 0:
            print(
                "ERROR: Param can not be empty, at least one param have to be provided ex: Param(var='test')")
            sys.exit(1)

        if len(kwargs) > 2:
            print("ERROR: A maximum of two parameters can be passed,"
                  "the parameter and the doc for the parameter ex: Param(db='test', doc='databaset name')")
            sys.exit(1)

        name = list(kwargs.keys())[0]
        doc = None
        if len(kwargs) == 2:
            if "doc" in kwargs:
                doc = kwargs["doc"]
                del kwargs["doc"]
            else:
                print(f"ERROR: in Parameter {name}, doc parameter not provide. {os.linesep}"
                      "Two parameters can be provided but the second one have to be 'doc' "
                      "ex: Param(db='test', doc='databaset name')")
                sys.exit(1)

        name = list(kwargs.keys())[0]
        value = kwargs[name]
        config = Config()
        config.__fromparam__ = True
        config[name] = value
        if doc is not None:
            config.__docs__[name] = doc
        return config


class ConfigGenerator:
    config = Config()

    config += Param(host="0.0.0.0", doc="Hostname or ip for flask server.")

    config += Param(port=8080,
                    doc="Port for flask server.")

    config += Param(log_file="hunabku.log",
                    doc="Name for logging file. "
                        "This is only enable in logging level different to DEBUG.")

    config += Param(use_reloader=True,
                    doc="Flask allows to reload the endpoint if something is changed in the code.\n"
                        "Set this False to void reload code.")

    config += Param(info_level=logging.DEBUG,
                    doc="The logging level, default DEBUG, set it to INFO for production.")

    config += Param(apikey=os.environ["HUNABKU_APIKEY"] if "HUNABKU_APIKEY" in os.environ else "colavudea",
                    doc="Apikey for authentication."
                    )

    config += Param(plugin_prefix="hunabku",
                    doc="Hunabku search the plugins using the prefix hunabku,"
                        "but if you want to personalize your own server you can change the prefix"
                    )

    config.apidoc += Param(apidoc_dir='hunabku_website',
                           doc="apidocs output directoy"
                           )
    config.apidoc += Param(use_https=False,
                           doc="apidocs output uses http/https"
                           )
    config.apidoc += Param(show_port=True,
                           doc="apidocs output show port of the server"
                           )

    def generate_config(self, output_file, hunabku, overwrite):
        if len(hunabku.plugins) == 0:
            hunabku.load_plugins(verbose=False)

        output = "from hunabku.Config import Config" + os.linesep
        output += "config = Config()" + os.linesep * 2
        output += "######################################" + os.linesep
        output += "# Hunabku Server config options below" + os.linesep
        output += "######################################" + os.linesep

        config_dict = self.parse_config(self.config)
        config_dict = self.parse_paths(config_dict)
        output += self.generate_output(config_dict)

        self.config = Config()

        # appening plugins documentatiom to current object
        for plugin in hunabku.plugins:
            if plugin["package"] not in self.config.keys():
                self.config[plugin["package"]] = Config()

            if plugin["mod_name"] not in self.config[plugin["package"]].keys():
                self.config[plugin["package"]][plugin["mod_name"]] = Config()

            self.config[plugin["package"]][plugin["mod_name"]
                                           ][plugin["class_name"]] = plugin['class'].config
        config_dict = self.parse_config(self.config)
        config_dict = self.parse_paths(config_dict)

        output += "##################################################" + os.linesep
        output += "# Hunabku Plugins config options below" + os.linesep
        output += "##################################################" + os.linesep
        output += "# The structure for config plugins are:" + os.linesep
        output += "# config.hunabku_plugin.File.Class.option = value" + os.linesep
        output += "##################################################" + os.linesep
        output += self.generate_output(config_dict)

        if overwrite:
            with open(output_file, "w") as f:
                f.write(output)
                f.close()
            return True
        else:
            if os.path.exists(output_file):
                return False
            else:
                with open(output_file, "w") as f:
                    f.write(output)
                    f.close()
                return True

    def generate_output(self, config_dict: dict):
        output = ""
        for key in config_dict.keys():
            last = key.split(".")[-1]
            output += f"# {last}" + os.linesep
            doc = config_dict[key]["doc"]
            value = config_dict[key]["value"]

            comments = doc.split(os.linesep)
            for comment in comments:
                output += f"#{comment}" + os.linesep

            if isinstance(value, str):
                output += f'{key} = "{value}"' + os.linesep * 2
            else:
                output += f'{key} = {value}' + os.linesep * 2
        return output

    def parse_config(self, config: Config, root=True) -> dict:
        """
        This method creates a dictionary from the config object
        """
        info = {}
        if root:
            cnf = Config()
            cnf.config = config
            config = cnf

        for key in config.keys():
            if isinstance(config[key], Config):
                if root:
                    info[key] = self.parse_config(config[key], False)
                else:
                    info[f".{key}"] = self.parse_config(config[key], False)
            else:
                value = config[key]
                doc = ""
                if key in config.__docs__:
                    doc = config.__docs__[key]
                info[key] = {'value': value, 'doc': doc}

        return info

    def parse_paths(self, config: dict, prefix="", root=True) -> dict:

        paths = {}

        for key, payload in config.items():
            if key == "config" and root:
                prefix = "config" + prefix
                _paths = self.parse_paths(config[key], prefix, False)
                paths.update(_paths)

            elif key.startswith("."):
                lprefix = prefix + key
                _paths = self.parse_paths(config[key], lprefix, False)
                paths.update(_paths)

            else:
                lprefix = prefix + '.' + key
                paths[lprefix] = payload

        return paths
