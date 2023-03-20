"""
A collection of environment utilities that can be used without circular dependencies.  For example,
should be usable inside django settings.py!
"""
import os
from datetime import datetime
from typing import Any, Tuple
from ubercode.utils.logging import ColorLogger
from ubercode.utils import convert

_utils_settings_logger = ColorLogger("utils.environment")


class Environment:
    """
    simple class to encapsulate overriding environment variable values if they exist
    """
    VARIABLE_DATA_TYPES = ["str", "bool", "int", "date"]
    DEFAULT_SECRET_PROPERTIES = ("PW", "PWD", "PASSWORD")

    def __init__(self, logger: ColorLogger = None, secret_properties: Tuple[str] = DEFAULT_SECRET_PROPERTIES, environment_variable_map = None):
        """
        Environment can be initialized with default values or overloaded as needed
        NOTE: environment_variable_map is for testing; should be left null and actually use os.env for production
        :param logger: optional ColorLogger to use; will default to internal logger @ info if not
        :param secret_properties: override the default values to mask the log values of a field (starts with)
        :param environment_variable_map: if provided will use this instead of os.env calls
        """
        self._logger = logger if logger else _utils_settings_logger
        self._secret_properties = []
        # secret properties should always be stripped and upper
        for prop in secret_properties:
            if prop:
                self._secret_properties.append(prop.strip().upper())
        self._env_map = environment_variable_map

    @staticmethod
    def infer_data_type(value):
        if value is not None:
            if isinstance(value, bool):
                return 'bool'
            if isinstance(value, str):
                return 'str'
            if isinstance(value, int):
                return 'int'
            if isinstance(value, datetime):
                return 'date'
        return 'str'

    def override_variable(self, variable_name: str, default_value: Any = None, environment_variable_name: str = None,
                          data_type: str = None, mask_log: bool = False):
        """
        Main purpose for override_variable is to replace the value if there is a specified environment variable.  It should
        also convert to a specified type if needed and log for communication.  NOTE: passwords and such should be masked.
        NOTE: for convenience, environment_variable_name only needs to be passed if different from variable_name
        Ex:
        DEBUG = True
        Env:
        DEBUG_OVERRIDE=False

        DEBUG = override_variable("DEBUG", True, "DEBUG_OVERRIDE", "bool")
        Would result in:
        DEBUG = False (of type boolean not string)

        :param data_type: ["str", "bool", "int", "date"] (default to str)
        :param variable_name: the variable name this value will be set as for logging purposes
        :param environment_variable_name: the environment variable to get the value from if it exists
        :param default_value: the default value to use if an environment variable does not exist
        :param mask_log: will mask the logged value if True
        :return: converted os value or default value passed
        """
        if not variable_name:
            raise ValueError("var_name must be passed!")
        if not environment_variable_name:
            environment_variable_name = variable_name
        _env_value = self._env_map.get(environment_variable_name) if self._env_map else os.environ.get(environment_variable_name)
        if _env_value is not None:
            if data_type is None or data_type not in self.VARIABLE_DATA_TYPES:
                # infer type from default value
                data_type = self.infer_data_type(default_value)
            # attempt to convert to datatype if not str
            if data_type == 'bool':
                _env_value = convert.to_bool(_env_value)
            if data_type == 'int':
                _env_value = convert.to_int(_env_value)
            if data_type == 'date':
                _env_value = convert.to_date(_env_value, none_to_now=False)
            _log_value = str(_env_value)
            _log_from_value = str(default_value)
            if data_type == 'str':
                if environment_variable_name.strip().upper() in self._secret_properties or mask_log:
                    _log_value = convert.to_mask(_env_value)
                    if _log_from_value != "None":
                        _log_from_value = convert.to_mask(_log_from_value)
            self._logger.info(f'overriding {variable_name}: [{str(_log_from_value)}] to [{str(_log_value)}]')
            return _env_value
        return default_value

    def override_database_variables(self, db_dict: dict, variable_name: str = "DATABASES") -> dict:
        """
        Overrides all database connection variables according to a set of rules.
        Expects: variable_name__connection_name__property=value
        For each match found, replaces the variable value in the settings file
        Ex:
        DATABASES = {
            'test': {
                'DRIVER': 'FreeTDS',
                # 'DRIVER': 'ODBC Driver 17 for SQL Server',
                'SERVER': 'localhost',
                'PORT': 1433,
                'DATABASE': 'test_db',
                'UID': 'test_user',
                'PWD': 'test_pwd',
                'TDS_VERSION': 7.2
            },
        }
        items:
        DATABASES__test__SERVER=docker.host.internal
        DATABASES__test__PWD=another_pwd

        Would result in:
        DATABASES = {
            'test': {
                'DRIVER': 'FreeTDS',
                # 'DRIVER': 'ODBC Driver 17 for SQL Server',
                'SERVER': 'docker.host.internal',
                'PORT': 1433,
                'DATABASE': 'test_db',
                'UID': 'test_user',
                'PWD': 'another_pwd',
                'TDS_VERSION': 7.2
            },
        }

        items_test = {
            'DATABASES__default__ENGINE': 'django.db.backends.mysql',
            'DATABASES__default__HOST': 'testdb.example.org',
            'DATABASES__default__NAME': 'test',
            'DATABASES__default__USER': 'testuser',
            'DATABASES__default__PASSWORD': 'Test_insecure_password',
            'DATABASES__default__PORT': 3306,
            }

        @param db_dict: The database dictionary to replace values in if found
        @param variable_name: Since we don't know the settings variable name with the dict passed in
            and the environment variable uses that to only apply values we want to the right database dict
            we need to say what the variable name is.  Defaults to Django DATABASES
        @return dict with replaced values
        """
        items = []
        if hasattr(self._env_map, "items"):
            items = self._env_map.items()
        elif hasattr(os.environ, "items"):
            items = os.environ.items()
        for k, v in items:
            # _logger.debug(f'key: {k} value: {v}')
            db_parts = k.split('__')
            # must at least have a DATABASES['key']['property'] to override the value
            if len(db_parts) == 3:
                # env must start with the varname we said we want to replace and have values for all parts
                if db_parts[0] and variable_name == db_parts[0] and db_parts[1] and db_parts[2]:
                    self._logger.debug(f'environment variable: {k}')
                    _log_from_value = 'None'
                    _log_to_value = str(v)
                    # we may be setting up a completely new database from scratch so create if it doesn't exist
                    if not db_dict[db_parts[1]]:
                        self._logger.debug(f'database {db_parts[0]}[{db_parts[1]}] was not found; creating...')
                        db_dict[db_parts[1]] = {}
                    # we now have db dict; we may not have a property already defined; if not we want to add it
                    if not db_dict[db_parts[1]].get(db_parts[2]):
                        self._logger.debug(
                            f'property {db_parts[0]}[{db_parts[1]}][{db_parts[2]}] was not found; creating...')
                        db_dict[db_parts[1]][db_parts[2]] = v
                    else:
                        self._logger.debug(
                            f'property {db_parts[0]}[{db_parts[1]}][{db_parts[2]}] was found; overriding...')
                        _log_from_value = str(db_dict[db_parts[1]][db_parts[2]])
                        # if we have an existing value and its secret be sure to mask it for logging before we override
                        if str(_log_from_value) != 'None' and db_parts[2].strip().upper() in self._secret_properties:
                            _log_from_value = convert.to_mask(str(_log_from_value))
                        db_dict[db_parts[1]][db_parts[2]] = v
                    # we may not mask from value because of 'None' for create but always mask to value if secret
                    if db_parts[2].strip().upper() in self._secret_properties:
                        _log_to_value = convert.to_mask(_log_to_value)
                    self._logger.info(
                        f'set {db_parts[0]}[{db_parts[1]}][{db_parts[2]}] from ['
                        f'{_log_from_value}] to [{_log_to_value}]')
                else:
                    if db_parts[0] and variable_name == db_parts[0]:
                        self._logger.warn(
                            f"{db_parts[0]}[{db_parts[1]}][{db_parts[2]}] has a database or property naming issue!")
        return db_dict
