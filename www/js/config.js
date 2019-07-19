// Backend address & port
var serverAddress = 'localhost';
var serverPort = '8001';
var allDataAllSeriesURL = "http://" + serverAddress + ":" + serverPort + "/all_data_all_series";
var dataWindowAllSeriesURL = "http://" + serverAddress + ":" + serverPort + "/data_window_all_series";
var dataWindowSingleSeriesURL = "http://" + serverAddress + ":" + serverPort + "/data_window_single_series";
var getAlertsURL = "http://" + serverAddress + ":" + serverPort + "/get_alerts";

// Series to display by default
// defaultSeries = ['HR', 'RR', 'BP', 'SpO2', 'CVP', 'ArtWave'];
defaultSeries = ['Numeric: HR.BeatToBeat', 'Numeric: RR.RR', 'Numeric: ART.Systolic', 'Numeric: ART.Diastolic', 'Numeric: SpO₂.SpO₂', 'CVP', 'ArtWave'];