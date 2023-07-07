import pytest
from auviewer import file as auvfile

@pytest.fixture
def f():
    f = auvfile.File(None, None, 'examples/sample_file.h5', None)
    yield f
    del f

def test_pattern_detection_high_threshold(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=None,
        thresholdhigh=4,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[284.0, 970.0], [2936.0, 3389.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=None,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_low_threshold(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-4,
        thresholdhigh=None,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[1604.0, 2189.0], [4371.0, 4509.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=None,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_high_and_low_threshold(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-4,
        thresholdhigh=4,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[284.0, 970.0], [1604.0, 2189.0], [2936.0, 3389.0], [4371.0, 4509.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_high_threshold_drop_above(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=None,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=2.5,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[291.0, 321.0], [931.0, 960.0], [2943.0, 3030.0], [3348.0, 3376.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=None,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=2.6,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_low_threshold_drop_below(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=None,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=-2.5,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[1638.0, 1654.0], [2141.0, 2180.0], [4373.0, 4478.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=None,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=-2.6,
        drop_values_above=None,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_high_and_low_thresholds_drop_above_and_below(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=-2.5,
        drop_values_above=2.5,
        drop_values_between=None,
    )
    assert patterns == expected

    expected = [[291.0, 321.0], [931.0, 960.0], [1638.0, 1654.0], [2141.0, 2180.0], [2943.0, 3030.0], [3348.0, 3376.0], [4373.0, 4478.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=-2.6,
        drop_values_above=2.6,
        drop_values_between=None,
    )
    assert patterns == expected

def test_pattern_detection_high_and_low_thresholds_drop_between(f):

    expected = []
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=[-5, 5],
    )
    assert patterns == expected

    expected = [[262.0, 978.0], [1582.0, 2200.0], [2895.0, 3449.0], [4258.0, 4589.0], [4640.0, 4640.0], [5686.0, 5727.0]]
    patterns = f.detectPatterns(
        type='patterndetection',
        series='/series_4:value',
        thresholdlow=-2.5,
        thresholdhigh=2.5,
        duration=30,
        persistence=.7,
        maxgap=50,
        expected_frequency=0,
        min_density=0,
        drop_values_below=None,
        drop_values_above=None,
        drop_values_between=[-2.5, 2.5],
    )
    assert patterns == expected