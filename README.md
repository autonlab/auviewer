# Medview Patient Data Viewer/Annotator

## API Methods

### Overview

A REST API is published for pulling patient data, making annotations, and other interactions.

API requests are submitted with GET http requests and, when applicable, GET parameters.

API responses are returned as JSON.

### Standard Data Response Format

All data series are delivered in the following standard JSON response format:

```json
{
    "seriesname": [
        [float:timeoffset, float:min, float:max, float:value],
        ...
    ],
    ...
}
```

The same format is used whether it is one series or multiple series, all time or time window.

The backend will decide whether to send downsampled values or real values and, for downsampled values, what scale of downsample to transmit. It decides this based on the goal of transmitting, at most, **M** downsampled values or 2**M** real values (**M** is configured in *server/config.py*).

For downsampled values, *min* & *max* will be defined and *value* will be null; conversely, for real values, *min* & *max* will be null and *value* will be defined.

If multiple series are requested, there may be a mix of series with downsampled values and series with real values. However, a given series will not have multiple types of values.

### /all_data_all_series

#### Request

http://[medview]/all_data_all_series

#### Response

See *Standard Data Response Format* above. All data series available for the patient for all time will be transmitted.

### /data_window_all_series

#### Request

http://[medview]/data_window_all_series?start=[float]&stop=[float]

The *start* & *stop* parameters are time offset floating-point values.

#### Response

See *Standard Data Response Format* above. All data series available for the patient in the given time window will be transmitted.

### /data_window_single_series

#### Request

http://[medview]/data_window_single_series?series=[string]start=[float]&stop=[float]

The *start* & *stop* parameters are time offset floating-point values, and the series is the URL-encoded name of the series.

#### Response

See *Standard Data Response Format* above. The requested data series in the given time window will be transmitted.

## Assumptions (TO BE FINALIZED)

* There is enough system memory to hold one entire series and one downsample level in memory with margin leftover for normal application overhead.