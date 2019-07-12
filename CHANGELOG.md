# Change Log

#### July 9, 2019

##### Technical

* Converted file processing to the new HDF5 file format from Jim.
* Got all previously working API functionality working after it was broken in the conversion to Cython downsampling.
* Added ability to add a graph while zoomed in without resetting the zoom to all time.

#### June 25, 2019

##### Technical

* Converted downsampling to Cython.

##### Documentation

* Added documentation of API methods to README.

#### June 18, 2019

##### Technical

* Added Flask web framework
* Added a timeout for shift/alt+mousewheel zooming to prevent many intermediary backend downsample requests mid-zoom. The timeout is 200ms, so there is virtually no degradation to user experience, and furthermore the requests don’t have to play “catch up”, which was a degradation of the interface.
* Converted the backend to work purely in floating-point time offsets instead of dates.
* Converted data preparation to list comprehensions & zips for to improve response efficiency.