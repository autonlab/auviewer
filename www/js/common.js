'use strict';

// Prints a message to console if verbose output is enabled
function vo() {
	if (config.verbose) {
		console.log.apply(null, arguments)
	}
}