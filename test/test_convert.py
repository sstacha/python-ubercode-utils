import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from datetime import datetime, timezone
from random import choice
from string import ascii_lowercase

from ubercode.utils import convert, logging

log = logging.ColorLogger("test_convert")


class TestConvert(unittest.TestCase):
    # -------- helper utilities ----------
    def test_strip(self):
        """ Tests the strip helper functon """
        # test normal whitespace stripping
        original_str = "   some str with spaces   "
        self.assertEqual("some str with spaces", convert.strip(original_str), "string was not stripped fully")
        self.assertEqual("some str with spaces   ", convert.strip(original_str, right=False), "left strip didn't work")
        self.assertEqual("   some str with spaces", convert.strip(original_str, left=False), "right strip didn't work")
        # test with dots instead for char replacement
        original_str = "...some str with dots..."
        self.assertEqual("some str with dots", convert.strip(original_str, strip_chars='.'),
                         "dot string was not stripped fully")
        self.assertEqual("some str with dots...", convert.strip(original_str, right=False, strip_chars='.'),
                         "left . strip didn't work")
        self.assertEqual("...some str with dots", convert.strip(original_str, left=False, strip_chars='.'),
                         "right . strip didn't work")
        # test None returns original value
        original_str = None
        self.assertEqual(None, convert.strip(original_str), "None string didn't return None")
        # test invalid value doesn't error but returns the original value
        original_str = 0
        self.assertEqual(0, convert.strip(original_str), "invalid value didn't return original value as expected")

    def test_dump(self):
        # test we can dump an instance of a variable like log and get its current values printed to stdout
        with redirect_stdout(StringIO()) as sout:
            convert.dump(log)
        log_output = sout.getvalue()
        self.assertTrue("'_level': 'INFO'" in log_output)
        self.assertTrue("'name': 'test_convert'" in log_output)
        # test that a non class item without a dict gives the string representation
        with redirect_stdout(StringIO()) as sout:
            convert.dump("Test String")
        log_output = sout.getvalue()
        # note: print adds a newline
        self.assertEqual(log_output, "Test String" + os.linesep)

    def test_human_readable(self):
        pass

    # -------- helper conversions ----------
    def test_mask(self):
        """ Tests the mask helper conversion function """
        # test normal masking for an expected value & that the shown limits to 6 chars
        original_str = "Some random password with spaces and #@!!$%^&"
        self.assertEqual("Some r*********************************!!$%^&", convert.to_mask(original_str))
        # test None returns original value
        self.assertEqual(None, convert.to_mask(None))
        # test empty string returns original value
        self.assertEqual("", convert.to_mask(""))
        # test all chars get masked up to 4
        for i in range(1 - 4):
            self.assertEqual(("*" * i), convert.to_mask("".join(choice(ascii_lowercase) for j in range(i))))
        # test chars shown increase to 2 when over 8 chars and that reminder still works
        self.assertEqual("12*****89", convert.to_mask("123456789"))

    # -------- primitive conversions --------
    def test_primitive_conversions(self):
        """ Tests the primitive conversion utility functions """

        # --- to_str
        # -----------
        # test that by default to_str will return an empty sting instead of 'None'
        self.assertEqual("", convert.to_str(None))
        # test that to_str will return the 'None' if none_to_empty is false
        self.assertEqual("None", convert.to_str(None, none_to_empty=False))

        # --- to_bool
        # -----------
        # None
        self.assertEqual(False, convert.to_bool(None), "None != False")
        # python True/False values
        self.assertEqual(True, convert.to_bool(True))
        self.assertEqual(False, convert.to_bool(False))
        # falsy string
        self.assertEqual(False, convert.to_bool(""))
        log.info("convert.to_bool: Testing false values " + str(convert.FALSE_VALUES))
        # truthy string that equates to a false value
        for false_value in convert.FALSE_VALUES:
            self.assertEqual(False, convert.to_bool(false_value))
        log.info("convert.to_bool: Testing true values " + str(convert.TRUE_VALUES))
        # true values
        for true_value in convert.TRUE_VALUES:
            self.assertEqual(True, convert.to_bool(true_value))
        # truthy value
        self.assertEqual(True, convert.to_bool("some string value"))

        # --- is_true_value
        # -----------------
        # truthy value that doesn't equate to true should be False
        self.assertEqual(False, convert.is_true("some string value"))
        log.info("convert.is_true: Testing true values " + str(convert.TRUE_VALUES))
        # true values should be True
        for true_value in convert.TRUE_VALUES:
            self.assertEqual(True, convert.is_true(true_value))
        # invalid value like date should be False
        self.assertEqual(False, convert.is_true(datetime.now()))

        # --- to_js_bool
        # --------------
        # None (invalid value) should be false
        self.assertEqual("false", convert.to_js_bool(None))
        # true
        self.assertEqual("true", convert.to_js_bool(True))
        # false
        self.assertEqual("false", convert.to_js_bool(False))
        # anything else (invalid value) should be false
        self.assertEqual("false", convert.to_js_bool("some string"))

        # --- to_int
        # ----------
        # None returns default by default
        self.assertEqual(0, convert.to_int(None))
        # None returns none if none_to_default is set to false
        self.assertEqual(None, convert.to_int(None, none_to_default=False))
        # we can override the default
        self.assertEqual(1, convert.to_int(None, default=1))
        # properly converts a boolean value
        self.assertEqual(1, convert.to_int(True))
        # note: changing default since it is already 0 by default
        self.assertEqual(0, convert.to_int(False, default=-1))
        # default is returned if we convert something invalid like a dict
        self.assertEqual(0, convert.to_int({"x": True, "y": True}))

        # --- to_none
        # -----------
        # NOTE: this is very handy to wrapper saving values that would put "None" or "" in database instead of null
        # None still returns None
        self.assertEqual(None, convert.to_none(None))
        # We can reset our values to convert to None: converts the string null or empty string to None only
        self.assertEqual(None, convert.to_none("null", values_to_convert=['null', '']))
        # values are stripped by default since many times these exist in databases
        self.assertEqual(None, convert.to_none("  None "))
        # but aren't when we turn the option off
        self.assertEqual("  None", convert.to_none("  None", strip_value=False))
        # original value is returned if we try something like a dict or object
        original_value = {"x": 1, "y": False}
        self.assertEqual(original_value, convert.to_none(original_value))

    # -------- date conversions --------
    def test_date_conversions(self):
        """ Tests the date conversion utility functions """

        # --- to_date
        # -----------
        # None generates a new aware date by default (UTC)
        now_convert = convert.to_date(None)
        now = datetime.now()
        # like now, utcnow will return an unaware datetime (tzinfo is None)
        utc_now = datetime.utcnow()
        # convert.to_date() will return a timezone aware datetime
        self.assertTrue(now_convert.tzinfo == timezone.utc)
        # now() and utcnow() will not; they return the time in the correct tz but don't tell us what they used (sucks!)
        self.assertIsNone(now.tzinfo)
        self.assertIsNone(utc_now.tzinfo)
        # now() returns local time not utc, so we can't compare times directly; just the dates
        self.assertNotEqual(now, now_convert)
        # but should match utcnow if we ignore the microsecond differences and explicitly set the tzinfo
        self.assertEqual(utc_now.replace(microsecond=0, tzinfo=timezone.utc), now_convert.replace(microsecond=0))
        # None returns None if we have the none_to_now set to false instead of new datetime
        self.assertEqual(None, convert.to_date(None, none_to_now=False))
        # note: to_date always returns a datetime use the date() function to compare just the date parts
        # todo: fix!  this doesn't work late at night since the hours = the next day from america/chicago -> utc after 6pm.
        # AssertionError: datetime.date(2026, 3, 3) != datetime.date(2026, 3, 4)
        # self.assertEqual(now.date(), now_convert.date())
        # if we convert both to local timezone and ignore microseconds they should be the same
        now_local = now.astimezone()
        now_convert_local = now_convert.astimezone()
        self.assertEqual(now_local.replace(microsecond=0), now_convert_local.replace(microsecond=0))
        # note: .astimezone() sets the tzinfo so these are aware datetimes now
        self.assertIsNotNone(now_local.tzinfo)
        self.assertIsNotNone(now_convert_local.tzinfo)
        # an invalid date pattern gives None
        self.assertEqual(None, convert.to_date("Not a Date!"))
        # let's test common patterns used by clients
        date = convert.to_date("2024-01-31 08:10:30")
        self.assertTrue(date is not None)
        self.assertEqual(date, convert.to_date("2024-01-31T08:10:30"))
        # note: the default iso8601 string doesn't support the compact form without dashes or colons in python3
        #   we have several clients that use this as a url parameter in the compact form
        self.assertEqual(date, convert.to_date("20240131T081030"))
        # and commonly passed as just the date without the time
        # note: stripping the time part using the date() method for comparison
        self.assertEqual(date.date(), convert.to_date("20240131").date())
        # bug fix: if a datetime is passed we get exception because datetime.fromisoformat(value) expects str only
        # we should just return the original value instead adding conditional to only alter if type str
        utc_now_tz = utc_now.replace(tzinfo=timezone.utc)
        self.assertEqual(utc_now_tz, convert.to_date(utc_now))


        # --- to_iso8601
        # --------------
        self.assertEqual("2024-01-31T08:10:30+00:00", convert.to_iso8601(date))


if __name__ == '__main__':
    unittest.main()
