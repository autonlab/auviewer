"""
This script generates some randomized test data, with potential edge cases included such as missing values or NaN values, and writes it to a new file.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import audata as aud
import datetime as dt
from pytz import UTC

render_plots = False
write_to_file = True

def generate_time_series(num_values, num_missing, num_gaps, signal_type='sin', frequency=1, amplitude=1):
    # Generate the values.
    time_seconds = np.array([i for i in range(num_values+num_gaps)], dtype=np.float32)

    if signal_type == 'sin':
        values = amplitude * np.sin(2 * np.pi * frequency * time_seconds / num_values)  # Create a sinusoidal wave.
    elif signal_type == 'ecg':
        values = amplitude * np.sin(2 * np.pi * frequency * time_seconds / num_values) * np.exp(-time_seconds / num_values)  # Damped sine wave.
    elif signal_type == 'random':
        values = np.random.randn(num_values+num_gaps)  # Random values.
    else:
        raise ValueError(f'Invalid signal_type: {signal_type}')

    values += np.random.randn(num_values+num_gaps) * 0.1  # Add some noise.

    # Randomly select some indices to replace with NaN.
    missing_indices = np.random.choice(range(num_values+num_gaps), size=num_missing, replace=False)
    values[missing_indices] = np.nan

    # Generate regular timestamps with a 1 second interval.
    timestamps = pd.date_range(start='1/1/2000', periods=num_values+num_gaps, freq='1S')

    # Randomly select some timestamps to remove for the gaps.
    gap_indices = np.random.choice(range(num_values+num_gaps), size=num_gaps, replace=False)
    timestamps = np.delete(timestamps, gap_indices)

    # convert timestamps to float32 offsets in seconds
    timestamps = (timestamps - timestamps[0]).total_seconds().astype(np.float32)

    return pd.DataFrame({
        'time': timestamps,
        'value': values[:len(timestamps)]
    })

# Generate the DataFrames and store them in a list.
dataframes = []
for i in range(10):
    if i < 3:  # Sinusoidal wave
        df = generate_time_series(10000, 1000, 200, signal_type='sin', frequency=i+1, amplitude=i+1)
    elif i < 6:  # ECG-like wave
        df = generate_time_series(10000, 1000, 200, signal_type='ecg', frequency=i+1, amplitude=i+1)
    else:  # Random values
        df = generate_time_series(10000, 1000, 200, signal_type='random')
    dataframes.append(df)

# define a function to plot a DataFrame
def plot_df(df, idx):
    plt.figure(figsize=(14,6))
    plt.plot(df['time'], df['value'], marker='o', markersize=2, linestyle='', label=f'DataFrame {idx}')
    plt.title(f'Time Series Plot for DataFrame {idx}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

# Render plots, if requested
if render_plots:
    for i, df in enumerate(dataframes):
        plot_df(df, i+1)

if write_to_file:
    f = aud.File.new('new_sample_file.h5', time_reference=dt.datetime(2020, 5, 4, tzinfo=UTC))
    for i, df in enumerate(dataframes):
        f[f'series_{i+1}'] = df
    f.close()