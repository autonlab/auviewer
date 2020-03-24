template = {

	# Not implemented
	'sidePanel': {
		'state': 'expanded'
	},

	'anomalyDetection': [],

	# Whether to display all series by default
	'defaultSeriesAll': True,

	# Series to display by default, if defaultSeriesAll==False
	'defaultSeries': [],

	'groups': [],

	# The TemplateSystem only expects the default project template to have a
	# single series defined called 'default'. Anything else is ignored.
	'series': {

		'default': {
			# soft and hard y-min & y-max
			# num seconds for x
			# increase data buffer size
			# for one chart, show simultaneously 10 min and 10 sec
			# put realtime stats ... or someting ... next to series
			# dots and/or lines
			# vertical line demarcation for events e.g. blood draw

			'graphHeight': '120px',
			'drawLine': False,
			'drawDots': True,
			'lineColor': '#171717',
			'dotColor': '#171717',
			'gridColor': 'rgb(232,122,128)',
			'ownAnomalyColor': '#f7a438',
			'otherAnomalyColor': '#f5d4ab',
			'ownCurrentWorkflowAnomalyColor': '#00bd1d', # '#cd7700', # was #00bd1d
			'otherCurrentWorkflowAnomalyColor': '#53ff65', # '#f5d4ab', # was #53ff65
			'ownAnnotationColor': 'rgba(0,72,182,0.73)',
			'ownAnnotationLabelColor': '#fff',
			'otherAnnotationColor': 'rgba(60,100,182,0.73)',
			'otherAnnotationLabelColor': '#fff'

		}

	}

}