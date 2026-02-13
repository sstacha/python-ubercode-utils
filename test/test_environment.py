import unittest
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ubercode.utils import logging, convert
from ubercode.utils.environment import Environment, Timer


class TestEnvironment(unittest.TestCase):

    # -------- environment class ----------
    def test_override_variable(self):
        os_vars = {"OVERRIDE_DEBUG": "False",
                   "TEST_DATE": "2023-02-21 08:30:00",
                   "TEST_INT": "1",
                   "PW": "abc1234def",
                   "TEST_STRING": "abc1234def"
                   }
        environment = Environment(environment_variable_map=os_vars)
        var = environment.override_variable("DEBUG", None, "OVERRIDE_DEBUG", 'bool')
        self.assertEqual(var, False)
        var = environment.override_variable("DEBUG", False)
        self.assertEqual(var, False)
        var = environment.override_variable("OVERRIDE_DEBUG", True)
        self.assertEqual(var, False)
        # test int conversion
        var = environment.override_variable("TEST_INT", 0)
        self.assertEqual(var, 1)
        # test date conversion
        dt = convert.to_date("2022-01-21 09:20:10")
        dteq = convert.to_date("2023-02-21 08:30:00")
        var = environment.override_variable("TEST_DATE", dt)
        self.assertEqual(var, dteq)
        var = environment.override_variable("TEST_DATE2", dt)
        self.assertEqual(var, dt)
        # test sending new logger
        logger = logging.ColorLogger("testlogger", level="Fatal")
        environment2 = Environment(environment_variable_map=os_vars, logger=logger)
        # ensure the new logger doesn't log output like before
        with redirect_stdout(StringIO()) as sout:
            environment2.override_variable("TEST_INT", 0)
        log_output = sout.getvalue()
        self.assertEqual(log_output, "")
        # test masking does nothing if not a string
        with redirect_stdout(StringIO()) as sout:
            var = environment.override_variable("TEST_DATE", dt)
        log_output = sout.getvalue()
        self.assertTrue("*" not in log_output)
        self.assertEqual(var, dteq)
        # test that masking works when asked (needs to be a string value)
        with redirect_stdout(StringIO()) as sout:
            var = environment.override_variable("PW", "test_password")
        log_output = sout.getvalue()
        self.assertEqual(log_output, "\x1b[94moverriding PW: [tes*******ord] to [ab******ef]\x1b[0m\n")
        # ensure the return value is the full password
        self.assertEqual(var, "abc1234def")
        # test masked if we tell it to mask
        with redirect_stdout(StringIO()) as sout:
            environment.override_variable("TEST_STRING", None, mask_log=True)
        log_output = sout.getvalue()
        self.assertEqual(log_output, "\x1b[94moverriding TEST_STRING: [None] to [ab******ef]\x1b[0m\n")

    def test_override_database_variables(self):
        # we will start with the default dict for a new django install
        BASE_DIR = Path(__file__).resolve().parent
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        os_vars = {
            "DATABASES__default__NAME": BASE_DIR / "sqlite.db",
            "TEST_DATE": "2023-02-21 08:30:00",
            "TEST_INT": "1",
            "PW": "abc1234def",
            "TEST_STRING": "abc1234def"
        }
        environment = Environment(environment_variable_map=os_vars)
        # test we can override just the database file name
        with redirect_stdout(StringIO()) as sout:
            DATABASES = environment.override_database_variables(DATABASES)
        print(f"override_vars password log output \n{sout.getvalue()}")
        self.assertEqual(DATABASES['default']['NAME'], BASE_DIR / "sqlite.db")
        # test we can take the default sqlite database and change it to a full mysql connection using env vars
        os_vars = {
            'DATABASES__default__ENGINE': 'django.db.backends.mysql',
            'DATABASES__default__HOST': 'testdb.example.org',
            'DATABASES__default__NAME': 'test',
            'DATABASES__default__USER': 'testuser',
            'DATABASES__default__PASSWORD': 'Test_insecure_password',
            'DATABASES__default__PORT': 3306,
        }
        environment = Environment(environment_variable_map=os_vars)
        # test we can override the default sqllite for dev laptops with a full mysql connection on a deployed server
        with redirect_stdout(StringIO()) as sout:
            DATABASES = environment.override_database_variables(DATABASES)
        print(f"override_vars log output \n{sout.getvalue()}")
        self.assertEqual(DATABASES['default']['ENGINE'], 'django.db.backends.mysql')
        self.assertEqual(DATABASES['default']['HOST'], 'testdb.example.org')
        self.assertEqual(DATABASES['default']['NAME'], 'test')
        self.assertEqual(DATABASES['default']['USER'], 'testuser')
        self.assertEqual(DATABASES['default']['PASSWORD'], 'Test_insecure_password')
        self.assertEqual(DATABASES['default']['PORT'], 3306)
        # test our password is encoded when logged
        self.assertTrue("Test_insecure_password" not in sout.getvalue())
        self.assertTrue("Test_************sword" in sout.getvalue())
        # test a None still works for initialization
        self.assertIsNotNone(Environment())

    def test_override_database_urls(self):
        # we will start with the default dict for a new django install
        BASE_DIR = Path(__file__).resolve().parent
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        db_override = BASE_DIR / "sqlite.db"
        os_vars = {
            "DJ_URL_default": f"://@/{db_override}",
#            "DATABASES__default__NAME": BASE_DIR / "sqlite.db",
            "TEST_DATE": "2023-02-21 08:30:00",
            "TEST_INT": "1",
            "PW": "abc1234def",
            "TEST_STRING": "abc1234def"
        }
        environment = Environment(environment_variable_map=os_vars)
        # test we can override just the database file name
        with redirect_stdout(StringIO()) as djurl_out:
            DATABASES = environment.override_database_urls(DATABASES)
        print(f"djurl password log output: \n{djurl_out.getvalue()}")

        self.assertEqual(DATABASES['default']['NAME'], str(db_override))
        # test we can take the default sqlite database and change it to a full mysql connection using env vars
        # os_vars = {
        #     'DATABASES__default__ENGINE': 'django.db.backends.mysql',
        #     'DATABASES__default__HOST': 'testdb.example.org',
        #     'DATABASES__default__NAME': 'test',
        #     'DATABASES__default__USER': 'testuser',
        #     'DATABASES__default__PASSWORD': 'Test_insecure_password',
        #     'DATABASES__default__PORT': 3306,
        # }
        os_vars = {
            'DJ_URL_default': 'django.db.backends.mysql://testuser:Test_insecure_password@testdb.example.org:3306/test'
        }
        environment = Environment(environment_variable_map=os_vars)
        # test we can override the default sqllite for dev laptops with a full mysql connection on a deployed server
        with redirect_stdout(StringIO()) as djurl_out:
            DATABASES = environment.override_database_urls(DATABASES)
        print(f"djurl full log output \n{djurl_out.getvalue()}")
        self.assertEqual(DATABASES['default']['ENGINE'], 'django.db.backends.mysql')
        self.assertEqual(DATABASES['default']['HOST'], 'testdb.example.org')
        self.assertEqual(DATABASES['default']['NAME'], 'test')
        self.assertEqual(DATABASES['default']['USER'], 'testuser')
        self.assertEqual(DATABASES['default']['PASSWORD'], 'Test_insecure_password')
        self.assertEqual(DATABASES['default']['PORT'], 3306)
        # test our password is encoded when logged
        self.assertTrue("Test_insecure_password" not in djurl_out.getvalue())


    def test_timer(self):
        timer = Timer().start()
        time.sleep(3)
        timer.stop()
        print(str(timer))
        self.assertEqual(timer.startTime.second + 3, timer.endTime.second)
        self.assertTrue(timer.duration.startswith('3'))


if __name__ == '__main__':
    unittest.main()
