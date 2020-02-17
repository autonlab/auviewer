'use strict';

let defProjConf = {

	// TODO
	useRandomAnomalyColors: false,
	seriesAnomalyColors: {},

	sidePanel: {
		'state': 'expanded'
	},

	// The TemplateSystem only expects the default project template to have a
	// single series defined called 'default'. Anything else is ignored.
	series: {

		default: {

			graphHeight: '100px',
			color: '#171717',
			gridColor: 'rgb(232,122,128)',
			ownAnomalyColor: '#f7a438',
			otherAnomalyColor: '#f5d4ab',
			ownCurrentWorkflowAnomalyColor: '#00bd1d', //'#cd7700', // was #00bd1d
			otherCurrentWorkflowAnomalyColor: '#53ff65', //'#f5d4ab', // was #53ff65
			ownAnnotationColor: 'rgba(0,72,182,0.73)',
			ownAnnotationLabelColor: '#fff',
			otherAnnotationColor: 'rgba(60,100,182,0.73)',
			otherAnnotationLabelColor: '#fff'

		}

	}

};