import pandas as pd 
import lfs
import gptapi



from snorkel.labeling import labeling_function

from snorkel.labeling.model import LabelModel
from snorkel.labeling import PandasLFApplier




df_train = pd.read_csv("/Users/qingyang/desktop/AutonLab/resuscitation-project/for_sophia") 


# Reference: Snorkel Labeling Model https://www.snorkel.org/use-cases/01-spam-tutorial

# Define the label mappings for convenience
ABSTAIN = -1
INSUFFICIENT = 0
SUFFICIENT = 1

# Apply the LFs to the unlabeled training data
applier = PandasLFApplier(gptapi.lfs_list)
L_train = applier.apply(df_train)
# L_train: label matrix, L[i, j] is the label that the jth labeling function output for the ith data point

# Train the label model and compute the training labels
label_model = LabelModel(cardinality=2, verbose=True)
label_model.fit(L_train, n_epochs=500, log_freq=50, seed=123)
df_train["label"] = label_model.predict(L=L_train, tie_break_policy="abstain")
