"""
A collection of conversion utilities that can be used without circular dependencies.
"""
import re
from typing import List, Any
from datetime import datetime, timezone
from pprint import pprint

# basic boolean true or false values
# NOTE: we will assume a to_lower conversion
TRUE_VALUES = [True, 1, "1", "y", "t", "true", "yes", "on"]
FALSE_VALUES = [None, False, 0, "0", "n", "f", "false", "no", "off"]


# -------- helper utilities ----------
def strip(value: str | None, strip_chars: str = None, left: bool = True, right: bool = True) -> str | None:
    """
    return stripped value if possible or original value
    :param value: str value to be stripped
    :param strip_chars: optional chars to strip (defaults to whitespace)
    :param left: (default = True) strip left
    :param right: (default = True) strip right
    :return: value (stripped if possible)
    """
    try:
        if left and right:
            return value.strip(strip_chars)
        if left:
            return value.lstrip(strip_chars)
        if right:
            return value.rstrip(strip_chars)
    except AttributeError:
        return value
    return value


def dump(value: Any, pretty=True) -> None:
    """
    Dumps the value to std out (either list of atts if obj or str if not)
    :param value: any value instance
    :param pretty: should we format the output using pprint
    :return: None (prints to stdout)
    """
    if hasattr(value, "__dict__"):
        if pretty:
            pprint(vars(value), indent=4)
        else:
            print(vars(value))
    else:
        print(str(value))


def to_human_readable(duration: int) -> str:
    days = duration // 86400
    hours = duration // 3600 % 24
    minutes = duration // 60 % 60
    seconds = duration % 60
    human_duration = ""
    if days >= 1:
        human_duration += f"{days} days, "
    if hours >= 1:
        human_duration += f"{hours} hours, "
    if minutes >= 1:
        human_duration += f"{minutes} minutes, "
    human_duration += f"{seconds:.2f} seconds"
    return human_duration


# -------- primitive conversions --------
def to_str(value: Any, none_to_empty: bool = True) -> str:
    """
    While not absolutely necessary; nice to have a common function to convert None values or not
    NOTE: this is exactly the same as [str(x) if x is not None else ''] if none_to_empty is true
    :param value: Any value
    :param none_to_empty: should we convert None to ''
    :return: string representation of the value
    """
    if none_to_empty and value is None:
        return ""
    return str(value)


def to_bool(value) -> bool:
    """
    Convert <value> to boolean.  Mainly handles returning false values passed as parameters which
    would otherwise return a truthy value.  Returns false if None or FALSE_VALUES, otherwise
    returns normal boolean truthy value conversion.
    :param value: expects int, bool, string or None
    :return: python True/False value
    """
    # note: need this line because strings and numbers are truthy and will return true
    if value in FALSE_VALUES or str(value).lower() in FALSE_VALUES:
        return False
    return bool(value)


def is_true(value: int | bool | str) -> bool:
    """
    Convert <value> to a True boolean value.  Useful when you want to convert a passed parameter to True if it matches
    one of the defined TRUE_VALUES above; otherwise False.
    NOTE: unlike to_bool does not use Truthy value so any value not defined in list is considered False period.
    EX: "somestring" = False instead of Truthy True value
    :param value: expects int, bool, string or None
    :return: python True/False value
    """
    if value is not None:
        if value in TRUE_VALUES or str(value).lower() in TRUE_VALUES:
            return True
    return False


def to_js_bool(bool_value: bool) -> str:
    """
    Convert python True/False to javascript string "true"/"false" for easily adding parameter to top of page scripts
    so javascript code can use.  Handy for placing context values from context into javascript variables on a page
    :param bool_value: expects python True/False value or None
    :return: Javascript string value "true"/"false"
    """
    if bool_value is True:
        return "true"
    return "false"


def to_int(value, default: int | None = 0, none_to_default: bool = True, suppress_warnings: bool = True) -> int | None:
    """
    Convert <value> to int.  Will always return integer or none instead of throwing exception
    @param value: value to be converted
    @param default: default value to use if none or error (defaults to 0 but set to None to have nulls in db)
    @param none_to_default: preserve a None value or convert to the default; Note: still checks default value afterwards
    @param suppress_warnings: suppress warning message during conversion exception
    @return: integer value or default or None depending on options
    """
    if value is None and not none_to_default:
        return None
    if value is None:
        value = default
    try:
        return int(value)
    except Exception:
        if not suppress_warnings:
            # if any exception occurs lets print to screen and then return the supplied default value
            print(f"WARNING: exception converting value {str(value)} to int; returning default value: {str(default)}!")
        return default


def to_none(value: Any, values_to_convert: List[str] = ('None', ''), strip_value=True):
    """
    Convert a string value to python None if it matches values_to_convert list of strings
    NOTE: this is helpful for converting string parameter values to None for storage in databases
    NOTE: we will strip the value first during comparison but not the value returned
    :param value: value to be converted
    :param values_to_convert: values to convert if matched
    :param strip_value: strip the value if possible (default True)
    :return: None if stripped string matches string in list otherwise the original value
    """
    if strip_value:
        value = strip(value)
    if str(value) in values_to_convert:
        return None
    return value


# -------- date conversions --------
def to_iso8601(value: datetime = None, tz: timezone = None) -> str:
    if not value:
        value = to_date()
    if tz:
        value = value.astimezone(tz)
    return value.isoformat(timespec='seconds')


def from_iso8601_compact(value: Any = None, tz: timezone = timezone.utc):
    _value = value
    if isinstance(value, str):
        if len(value.strip()) == 0:
            return None
        # remove colons and dashes EXCEPT for the dash indicating + or - utc offset for the timezone
        conformed_timestamp = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", "", value)
        _value = None
        try:
            _value = datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S.%f%z")
        except ValueError:
            try:
                _value = datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S.%f")
            except ValueError:
                try:
                    _value = datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S")
                except ValueError:
                    try:
                        _value = datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M")
                    except ValueError:
                        try:
                            _value = datetime.strptime(conformed_timestamp, "%Y%m%dT%H")
                        except ValueError:
                            try:
                                _value = datetime.strptime(conformed_timestamp, "%Y%m%d")
                            except ValueError:
                                raise ValueError(f"DateTime string [{value}] did not match an expected pattern.")
    if tz and isinstance(_value, datetime) and not _value.tzinfo:
        _value = _value.replace(tzinfo=tz)
    return _value


def to_date(value: Any = None, tz: timezone | None = timezone.utc, none_to_now: bool = True, suppress_warnings: bool = True):
    """
    Convert string to python date.  Currently, only concerned about iso8601 and db type formats.
    None returns current date by default but can be overridden with none_to_now optional parameter
    :param value: string value for date (currently only iso8601)
    :param tz: timezone (defaults to timezone.utc)
    :param none_to_now: override the default to return now if none is passed; primarily for db operations to store null
    :param suppress_warnings: suppress warning messages for exceptions during conversion
    :return: python date or None
    """
    if value is None:
        if none_to_now:
            return datetime.now(tz)
        else:
            return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            try:
                value = from_iso8601_compact(value)
            except ValueError:
                if not suppress_warnings:
                    print(f"WARNING: exception converting value {str(value)} to date; returning None!")
                return None
    if tz and isinstance(value, datetime) and not value.tzinfo:
        value = value.replace(tzinfo=tz)
    return value


# -------- helper conversions --------
def to_mask(value: str | None) -> str | None:
    _mask = value
    if isinstance(value, str) and value is not None and len(value) > 0:
        # if we are less than 4 chars then mask the entire string
        if len(value) < 4:
            return "*" * len(value)
        # if we are more than 4 chrs determine the number of chars to keep
        # lets go with a quarter of the characters up to a max of 6
        _iqtr = len(value) // 4
        if _iqtr > 6:
            _iqtr = 6
        _mask = value[:_iqtr]
        # append the masked values (length - iqtr * 2)
        _mask += "*" * (len(value) - (_iqtr * 2))
        # append the last quarter of the values up to 6 unmasked
        _mask += value[-_iqtr:]
    return _mask

def obj_to_str(obj, property_filter_list=None):
    """
    Mostly used for debugging.  Very useful to print the properties of an object on a line; condensing reasonably

    :param obj: the object to inspect properties for
    :param property_filter_list: any property names we want to omit
    :return: a string containing the outputted properties
    """
    attbuf = ""
    for key, value in vars(obj).items():
        if property_filter_list and key in property_filter_list:
            continue
        if not key.startswith('__'):
            if len(attbuf) > 0:
                attbuf += ", "
            # show the first 50 chars and last 25 chars
            this_content = str(value)
            this_content = this_content.replace('\n', ' ').replace('\r', '').strip()
            if this_content:
                if len(this_content) > 150:
                    attbuf += str(key) + ": [" + this_content[0:25] + " ... " + this_content[
                                                                                len(this_content) - 25:len(
                                                                                    this_content)] + "]"
                else:
                    attbuf += str(key) + ": " + this_content or ""
            else:
                attbuf += str(key) + ": " + this_content or ""
    return "[" + attbuf + "]"
