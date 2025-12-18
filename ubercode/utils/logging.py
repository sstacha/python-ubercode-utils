"""
A collection of logging utilities that can be used without circular dependencies.  For example,
should be usable inside django settings.py!  normal logging is not!
"""
import textwrap


def indent_string(text, amount, ch=' '):
    return textwrap.indent(text, amount * ch)


class TermColor:
    """
    Class to display output color around text printed in a terminal window
    USAGE IN MSG (color_output=False)
    NOTE: if color_output=True then the entire msg will be output in color based on log_level
    ---
    EX: print(TermColor.FAIL + "REMOVING: " + TermColor.ENDC + os.path.join(dirpath, name))
    """

    def __init__(self):
        pass

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    F_Default = "\x1b[39m"
    F_Black = "\x1b[30m"
    F_Red = "\x1b[31m"
    F_Green = "\x1b[32m"
    F_Yellow = "\x1b[33m"
    F_Blue = "\x1b[34m"
    F_Magenta = "\x1b[35m"
    F_Cyan = "\x1b[36m"
    F_LightGray = "\x1b[37m"
    F_DarkGray = "\x1b[90m"
    F_LightRed = "\x1b[91m"
    F_LightGreen = "\x1b[92m"
    F_LightYellow = "\x1b[93m"
    F_LightBlue = "\x1b[94m"
    F_LightMagenta = "\x1b[95m"
    F_LightCyan = "\x1b[96m"


class ColorLogger:
    """
    Class to encapsulate methods and data for logging at a specific log level with terminal colors
    TODO: figure out if we can somehow integrate this into django logging
    """
    # static constant values for determining log level by index low to high
    #   NOTE: requires all indexes to increment obviously in order to have different logging levels
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARN', 'FATAL', 'ALWAYS']
    # default color mapping for each helper function
    # NOTE: can be overridden after creation to change all future color calls for a helper function like .info()
    DEFAULT_COLOR_MAP = {
        'DEBUG': TermColor.F_DarkGray,
        'INFO': TermColor.OKBLUE,
        'SUCCESS': TermColor.OKGREEN,
        'WARN': TermColor.WARNING,
        'FATAL': TermColor.FAIL,
        'ALWAYS': TermColor.F_Default
    }

    # I would really like to turn this into a Literal (python 3.8) but I don't want to force that just yet
    #   however, I am going to try and change the accepted params to be string to fit more with django.logging
    #   even if I can't use the Literal helper for tools pre runtime right now.  Consider TermColor param Literal too.
    # example literal code:
    # start with the literal
    # Argument = typing.Literal['DEBUG', 'INFO' ...]
    # build the list of accepted values from literal so it doesn't affect the lookups
    # VALID_ARGUMENTS: typing.Tuple[Argument, ...] = typing.get_args(Argument)
    # or
    # VALID_ARGUMENTS: typing.List[Argument] = list(typing.get_args(Argument))
    # NOTE: maybe do a generator to create the dict of values or use index if list stays in order (should)
    def __init__(self, name: str, level: str or int or None = None, color_output: bool = True):
        self.name = name
        self._level = self.get_initial_log_level(level)
        self.level = self._level
        self.indention = 0
        self.indent_spaces = 4
        self.color_output = color_output
        self.repeat_msg = '.'
        self.repeat_max = 100
        self.repeat_cnt = 0
        self.repeat_indention = 0

    # logging helper functions
    def get_initial_log_level(self, value: str or int or None) -> str:
        """
        sets the initial value; for the default settings implementation this will simply be INFO
            or a valid value the developer gave us; for logging implementation this will be overridden
            to include a settings value check for the specified logger name
        @param value: default the developer would like or INFO
        @return: one of ColorLogger.LOG_LEVELS[]
        """
        # in our base implementation that settings can use this simply defaults to INFO or passes
        #   whatever value was passed in
        if value is not None:
            # we have a possible value could be int; validate and return or default below
            if isinstance(value, int):
                # try and convert to string value from array if in range
                if len(ColorLogger.LOG_LEVELS) > value >= 0:
                    value = ColorLogger.LOG_LEVELS[value]
            # we should have a value; if valid return
            if value.upper() in ColorLogger.LOG_LEVELS:
                return value.upper()
        # we don't have a valid value so default
        return 'INFO'

    @staticmethod
    def to_valid_level(level: str or int) -> str:
        """
        validate and return string version of LOG_LEVEL to use from LOG_LEVELS
        @param level: passed level value (int or string)
        @return: string log level value from LOG_LEVELS
        """
        # for backwards compatability if we pass an int (index) convert it
        if isinstance(level, int):
            if 0 <= level < len(ColorLogger.LOG_LEVELS):
                level = ColorLogger.LOG_LEVELS[level]
            else:
                raise ValueError(
                    f"ColorLogger.level [{str(level)}] must be one of {str(ColorLogger.LOG_LEVELS)} or the index")
        # last check to make sure our string is in the list of accepted values
        if level not in ColorLogger.LOG_LEVELS:
            raise ValueError(
                f"ColorLogger.level [{str(level)}] must be one of {str(ColorLogger.LOG_LEVELS)} or the index")
        return level

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, value: str or int) -> None:
        self._level = self.to_valid_level(value)

    def indent(self) -> int:
        self.indention += 1
        return self.indention

    def unindent(self) -> int:
        self.indention -= 1
        if self.indention < 0:
            self.indention = 0
        return self.indention

    def debug(self, msg: str, color: str = DEFAULT_COLOR_MAP['DEBUG'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'DEBUG', color, indent, end)

    def info(self, msg: str, color: str = DEFAULT_COLOR_MAP['INFO'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'INFO', color, indent, end)

    def success(self, msg: str, color: str = DEFAULT_COLOR_MAP['SUCCESS'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'INFO', color, indent, end)

    def warn(self, msg: str, color: str = DEFAULT_COLOR_MAP['WARN'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'WARN', color, indent, end)

    def fatal(self, msg: str, color: str = DEFAULT_COLOR_MAP['FATAL'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'FATAL', color, indent, end)

    def always(self, msg: str, color: str = DEFAULT_COLOR_MAP['ALWAYS'], indent: int = None, end: str = None) -> None:
        self.log(msg, 'ALWAYS', color, indent, end)

    def log(self, msg: str, log_level: str or int, color: str = None, indent: int = None, end: str = None) -> None:
        """
        If we have a color and want color output we print it with color otherwise we just print it to screen
        :param msg: message to display
        :param log_level: the level for this message
        :param color: the color to use (SEE TermColor constants)
        :param indent: override indention otherwise uses indention property on logger
        :param end: pass end to print if exists to keep on same line for example
        :return: None; prints to screen with the proper color
        """
        log_level = self.to_valid_level(log_level)
        if self.LOG_LEVELS.index(log_level) >= self.LOG_LEVELS.index(self.level):
            c_msg = str(msg)
            if self.color_output and color:
                c_msg = color + c_msg + TermColor.ENDC
            if str(msg) == self.repeat_msg:
                # the first time we start repeating track the indent level
                if not self.repeat_cnt:
                    if indent is not None:
                        self.repeat_indention = indent
                    else:
                        self.repeat_indention = self.indention
                    c_msg = indent_string(c_msg, self.repeat_indention * self.indent_spaces)
                self.repeat_cnt += 1
                if self.repeat_cnt > self.repeat_max:
                    # include the newline and index
                    c_msg = f'\n{indent_string(c_msg, self.repeat_indention * self.indent_spaces)}'
                    # reset out skipped message to our current length
                    self.repeat_cnt = 1
            else:
                if self.repeat_cnt:
                    c_msg = '\n' + c_msg
                    self.repeat_cnt = 0
                if indent is not None:
                    c_msg = indent_string(c_msg, indent * self.indent_spaces)
                elif self.indention is not None:
                    c_msg = indent_string(c_msg, self.indention * self.indent_spaces)

            if end is not None:
                print(c_msg, end=end)
            else:
                print(c_msg)
