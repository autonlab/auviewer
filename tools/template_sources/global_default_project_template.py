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
			'series': 'numerics/HR/data',
			'tlow': 58,
			'thigh': 110,
			'dur': 10,
			'duty': 70,
			'maxgap': 1800
		},
		{
			'series': 'numerics/HR.HR/data',
			'tlow': 58,
			'thigh': 110,
			'dur': 10,
			'duty': 70,
			'maxgap': 1800
		},
		{
			'series': 'numerics/rRR/data',
			'tlow': 10,
			'thigh': 29,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/RR.RR/data',
			'tlow': 10,
			'thigh': 29,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/NBP-S/data',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/NBP-M/data',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/NBPs/data',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/NBPm/data',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/AR1-S/data',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/AR1-M/data',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/ART.Systolic/data',
			'tlow': 90,
			'thigh': 165,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/ART.Mean/data',
			'tlow': 65,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/SpO₂.SpO₂/data',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/SpO₂T.SpO₂T/data',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		},
		{
			'series': 'numerics/SPO2-%/data',
			'tlow': 90,
			'dur': 300,
			'duty': 70,
			'maxgap': 300
		}
	],

	# Series to display by default
	'defaultSeries': [
		'numerics/HR/data',
		'numerics/HR.HR/data',
		'numerics/HR.BeatToBeat/data',
		'numerics/rRR/data',
		'numerics/RR.RR/data',
		'numerics/SpO₂.SpO₂/data',
		'numerics/SpO₂T.SpO₂T/data',
		'numerics/SPO2-%/data',
		'CVP/data',
		'ArtWave/data',
		"Group:\nnumerics/AR1-D/data\nnumerics/AR1-S/data\nnumerics/AR1-M/data",
		"Group:\nnumerics/ART.Diastolic/data\nnumerics/ART.Systolic/data\nnumerics/ART.Mean/data",
		"Group:\nnumerics/NBP.NBPd/data\nnumerics/NBP.NBPm/data\nnumerics/NBP.NBPs/data",
		"Group:\nnumerics/NBP-D/data\nnumerics/NBP-M/data\nnumerics/NBP-S/data"
		"Group:\nSignal 3\nSignal 4\nSignal 5"
	],

	'groups': [
		['numerics/AR1-D/data', 'numerics/AR1-S/data', 'numerics/AR1-M/data'],
		['numerics/ART.Diastolic/data', 'numerics/ART.Systolic/data', 'numerics/ART.Mean/data'],
		['numerics/NBP.NBPd/data', 'numerics/NBP.NBPm/data', 'numerics/NBP.NBPs/data'],
		['numerics/NBP-D/data', 'numerics/NBP-M/data', 'numerics/NBP-S/data'],
		['Signal 3', 'Signal 4', 'Signal 5']
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
		'numerics/AR1-D/data': bpSeries,
		'numerics/AR1-M/data': bpSeries,
		'numerics/AR1-S/data': bpSeries,
		'numerics/ART.Diastolic/data': bpSeries,
		'numerics/ART.Mean/data': bpSeries,
		'numerics/ART.Systolic/data': bpSeries,
		'numerics/NBP.NBPd/data': bpSeries,
		'numerics/NBP.NBPm/data': bpSeries,
		'numerics/NBP.NBPs/data': bpSeries,
		'numerics/NBP.NBP-D/data': bpSeries,
		'numerics/NBP.NBP-M/data': bpSeries,
		'numerics/NBP.NBP-S/data': bpSeries,

		# Pulse Series
		'numerics/ART.Pulse/data': pulseSeries,
		'numerics/NBP.Pulse/data': pulseSeries,
		'numerics/SpO₂.Pulse/data': pulseSeries,

		# SPO2 Series
		'numerics/SpO₂.SpO₂/data': spo2Series,
		'numerics/SpO₂T.SpO₂T/data': spo2Series,
		'numerics/SPO2-%/data': spo2Series,

		# Other Series
		'numerics/RR.RR/data': {
			'range': [0, 50]
		}

	}

}