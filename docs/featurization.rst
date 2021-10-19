AUViewer takes a modular approach to featurization. It comes with a library of featurization modules, and you can also add your own.

Each featurizer must specify two things:

* Parameters (required and optional)
* Feature generator function

A featurizer may also provide:

* Documentation (may use HTML markup)

A featurizer should return a scalar value based on the time series provided to it. AUViewer enables rolling window operations using featurizers, but the featurizer operates agnostic of this.

