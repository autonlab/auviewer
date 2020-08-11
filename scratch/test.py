import audata as aud
import h5py as h5
import pandas as pd

f = aud.File.new('events_sample.h5', overwrite=True)

of = h5.File('/zfsauton/data/public/gwelter/AUView/originals/conditionc/20190805_1361133_1854848.h5', 'r')

cedata = of['ce']['all']['data'][()]

cestrings = of['ce']['all']['strings'][()]

f['ce'] = pd.DataFrame(
    data={
        'time': cedata['date'],
        'eventName': pd.Series([cestrings[i] for i in cedata['eventName']], dtype='category'),
        'resultVal': cedata['resultVal'],
        'resultUnit': pd.Series([cestrings[i] for i in cedata['resultUnit']], dtype='category'),
        'resultStat': pd.Series([cestrings[i] for i in cedata['resultStat']], dtype='category')
    }
)

print(f['ce'])

f.close()

# date -> time
# eventName (string)
# resultVal (float)
# resultUnit (string)
# resultStat (string)