bpSeries = {
	'range': [0, 250]
}
pulseSeries = {
	'range': [0, 200]
}
spo2Series = {
	'range': [30, 100]
}

template = {

	# Not implemented
	'sidePanel': {
		'state': 'expanded'
	},

	'anomalyDetection': [
		{
			'series': '/data/numerics/HR:value',
			'tlow': 58,
			'thigh': 110,
			'dur': 10,
			'duty': 70,
			'maxgap': 1800
		},
		{
			'series': '/data/numerics/HR.HR:value',
			'tlow': 58,
			'thigh': 110,
			'dur': 10,
			'duty': 70,
			'maxgap': 1800
		},
		{
			'series': '/data/numerics/rRR:value',
			'tlow': 10,
			'thigh': 29,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/RR.RR:value',
			'tlow': 10,
			'thigh': 29,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/NBP-S:value',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/NBP-M:value',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/NBPs:value',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/NBPm:value',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/AR1-S:value',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/AR1-M:value',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/ART.Systolic:value',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/ART.Mean:value',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/SpO₂.SpO₂:value',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/SpO₂T.SpO₂T:value',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': '/data/numerics/SPO2-%:value',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		}
	],

	# Whether to display all series by default
	'defaultSeriesAll': False,

	# Series to display by default
	'defaultSeries': [
		'/data/numerics/HR:value',
		'/data/numerics/HR.HR:value',
		'/data/numerics/HR.BeatToBeat:value',
		'/data/numerics/rRR:value',
		'/data/numerics/RR.RR:value',
		'/data/numerics/SpO₂.SpO₂:value',
		'/data/numerics/SpO₂T.SpO₂T:value',
		'/data/numerics/SPO2-%:value',
		'CVP:value',
		'ArtWave:value',
		"Group:\n/data/numerics/AR1-D:value\n/data/numerics/AR1-S:value\n/data/numerics/AR1-M:value",
		"Group:\n/data/numerics/ART.Diastolic:value\n/data/numerics/ART.Systolic:value\n/data/numerics/ART.Mean:value",
		"Group:\n/data/numerics/NBP.NBPd:value\n/data/numerics/NBP.NBPm:value\n/data/numerics/NBP.NBPs:value",
		"Group:\n/data/numerics/NBP-D:value\n/data/numerics/NBP-M:value\n/data/numerics/NBP-S:value"
	],

	'groups': [
		['/data/numerics/AR1-D:value', '/data/numerics/AR1-S:value', '/data/numerics/AR1-M:value'],
		['/data/numerics/ART.Diastolic:value', '/data/numerics/ART.Systolic:value', '/data/numerics/ART.Mean:value'],
		['/data/numerics/NBP.NBPd:value', '/data/numerics/NBP.NBPm:value', '/data/numerics/NBP.NBPs:value'],
		['/data/numerics/NBP-D:value', '/data/numerics/NBP-M:value', '/data/numerics/NBP-S:value']
	],

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

		},

		# BP Series
		'/data/numerics/AR1-D:value': bpSeries,
		'/data/numerics/AR1-M:value': bpSeries,
		'/data/numerics/AR1-S:value': bpSeries,
		'/data/numerics/ART.Diastolic:value': bpSeries,
		'/data/numerics/ART.Mean:value': bpSeries,
		'/data/numerics/ART.Systolic:value': bpSeries,
		'/data/numerics/NBP.NBPd:value': bpSeries,
		'/data/numerics/NBP.NBPm:value': bpSeries,
		'/data/numerics/NBP.NBPs:value': bpSeries,
		'/data/numerics/NBP.NBP-D:value': bpSeries,
		'/data/numerics/NBP.NBP-M:value': bpSeries,
		'/data/numerics/NBP.NBP-S:value': bpSeries,

		# Pulse Series
		'/data/numerics/ART.Pulse:value': pulseSeries,
		'/data/numerics/NBP.Pulse:value': pulseSeries,
		'/data/numerics/SpO₂.Pulse:value': pulseSeries,

		# SPO2 Series
		'/data/numerics/SpO₂.SpO₂:value': spo2Series,
		'/data/numerics/SpO₂T.SpO₂T:value': spo2Series,
		'/data/numerics/SPO2-%:value': spo2Series,

		# Other Series
		'/data/numerics/RR.RR:value': {
			'range': [0, 50]
		}

	}

}