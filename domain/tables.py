"""Transformaciones de tablas que no dependen de Streamlit."""

import math


def numeric_columns(frame, columns):
    result = frame.copy()
    for column in columns:
        if column in result.columns:
            result[column] = result[column].apply(_number_or_zero)
    return result


def _number_or_zero(value):
    try:
        number = float(value)
        return 0.0 if math.isnan(number) else number
    except (TypeError, ValueError):
        return 0.0
