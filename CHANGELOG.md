# Change Log

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