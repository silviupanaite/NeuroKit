# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np


from .ecg_hrv import ecg_hrv


def ecg_intervalrelated(data, sampling_rate=1000):
    """
    Performs ECG analysis on longer periods of data (typically > 10 seconds),
    such as resting-state data.

    Parameters
    ----------
    data : DataFrame, dict
        A DataFrame containing the different processed signal(s) as
        different columns, typically generated by `ecg_process()` or
        `bio_process()`. Can also take a dict containing sets of
        separately processed DataFrames.
    sampling_rate : int
        The sampling frequency of the signal (in Hz, i.e., samples/second).

    Returns
    -------
    DataFrame
        A dataframe containing the analyzed ECG features. The analyzed
        features consist of the following:
        - *"ECG_Rate_Mean"*: the mean heart rate.
        - *"ECG_HRV"*: the different heart rate variability metrices.
        See `ecg_hrv()` docstrings for details.

    See Also
    --------
    bio_process, ecg_eventrelated

    Examples
    ----------
    >>> import neurokit2 as nk
    >>>
    >>> # Download data
    >>> data = nk.data("bio_resting_5min_100hz")
    >>>
    >>> # Process the data
    >>> df, info = nk.ecg_process(data["ECG"], sampling_rate=100)
    >>>
    >>> # Single dataframe is passed
    >>> nk.ecg_intervalrelated(df)
    >>>
    >>> epochs = nk.epochs_create(df, events=[0, 15000], sampling_rate=100, epochs_end=150)
    >>> nk.ecg_intervalrelated(epochs)
    """
    intervals = {}

    # Format input
    if isinstance(data, pd.DataFrame):
        rate_cols = [col for col in data.columns if 'ECG_Rate' in col]
        if len(rate_cols) == 1:
            intervals.update(_ecg_intervalrelated_formatinput(data))
            intervals.update(_ecg_intervalrelated_hrv(data, sampling_rate))
        else:
            raise ValueError("NeuroKit error: ecg_intervalrelated(): Wrong input,"
                             "we couldn't extract heart rate. Please make sure"
                             "your DataFrame contains an `ECG_Rate` column.")
        ecg_intervals = pd.DataFrame.from_dict(intervals,
                                               orient="index").T

    elif isinstance(data, dict):
        for index in data:
            intervals[index] = {}  # Initialize empty container

            # Format dataframe
            data[index] = data[index].set_index('Index').drop(['Label'], axis=1)

            # Rate
            intervals[index] = _ecg_intervalrelated_formatinput(data[index],
                                                                intervals[index])

            # HRV
            intervals[index] = _ecg_intervalrelated_hrv(data[index], sampling_rate,
                                                        intervals[index])

        ecg_intervals = pd.DataFrame.from_dict(intervals, orient="index")

    return ecg_intervals

# =============================================================================
# Internals
# =============================================================================


def _ecg_intervalrelated_formatinput(data, output={}):

    # Sanitize input
    colnames = data.columns.values
    if len([i for i in colnames if "ECG_Rate" in i]) == 0:
        raise ValueError("NeuroKit error: ecg_intervalrelated(): Wrong input,"
                         "we couldn't extract heart rate. Please make sure"
                         "your DataFrame contains an `ECG_Rate` column.")
        return output

    signal = data["ECG_Rate"].values
    output["ECG_Rate_Mean"] = np.mean(signal)

    return output


def _ecg_intervalrelated_hrv(data, sampling_rate, output={}):

    hrv = ecg_hrv(data, sampling_rate=sampling_rate)
    for column in hrv.columns:
        output[column] = float(hrv[column])

    return output
