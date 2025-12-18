""" common utilities for working with dataframes"""
from typing import Any
from . import logging
from datetime import datetime

default_date_formats = {
    'date': '%Y-%m-%d',
    'datetime': '%Y-%m-%d %H:%M:%S',
    'datetimemilli': '%Y-%m-%d %H:%M:%S.%f'
}

def to_date_str(date_string: str or None, date_col: str, date_field_map: dict, date_formats: dict) -> str or None:
    if date_string == 'None' or date_string == 'NaT' or not date_string:
        return None
    if '.' in date_string:
        dt = datetime.strptime(date_string, date_formats['datetimemilli'])
    elif ':' in date_string:
        dt = datetime.strptime(date_string, date_formats['datetime'])
    else:
        dt = datetime.strptime(date_string, date_formats['date'])
    if not dt:
        return None
    return dt.strftime(date_formats[date_field_map[date_col]])

# extend the logging to include log.dataframe()
# NOTE: making dataframe type Any, so we don't have to include pandas but intended use is dataframe
# todo: decide if better to include in different install requiring pandas like the requests utils version
class DataframeLogger(logging.ColorLogger):
    def dataframe(self, dataframe: Any,  label: str = None, color: str = "INFO", df_color: str = "ALWAYS") -> None:
        color = DataframeLogger.DEFAULT_COLOR_MAP.get(color, DataframeLogger.DEFAULT_COLOR_MAP["INFO"])
        df_color = DataframeLogger.DEFAULT_COLOR_MAP.get(df_color, DataframeLogger.DEFAULT_COLOR_MAP["ALWAYS"])
        if label:
            self.always(label, color=color)
        # print(dataframe)
        self.always(str(dataframe), color=df_color)
