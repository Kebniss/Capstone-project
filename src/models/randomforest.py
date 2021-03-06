""" This script loads the dense training data, encodes the target labels and
    trains a random forest model using CV. The best estimator is saved"""
''' THIS MODEL WITH MY FEATURES OBTAINS A SCORE OF 2.38088 ON KAGGLE'''

import os
import pickle
import numpy as np
import pandas as pd
from os import path
import seaborn as sns
from time import time
from scipy import sparse, io
import matplotlib.pyplot as plt
from sklearn.metrics import log_loss
from dotenv import load_dotenv, find_dotenv
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import LabelEncoder
from sklearn.grid_search import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.cross_validation import train_test_split
from sklearn.metrics import make_scorer, f1_score, confusion_matrix
from sklearn.calibration import calibration_curve, CalibratedClassifierCV

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

RAW_DATA_DIR = os.environ.get("RAW_DATA_DIR")
FEATURES_DATA_DIR = os.environ.get("FEATURES_DIR")
MODELS_DIR = os.environ.get("MODELS_DIR")

data = pd.read_csv(path.join(FEATURES_DATA_DIR, 'dense_train_p_al_d.csv'))
gatrain = pd.read_csv(os.path.join(RAW_DATA_DIR,'gender_age_train.csv'),
                      index_col='device_id')

labels = gatrain['group']
targetencoder = LabelEncoder().fit(labels) # encoding target labels
labels = targetencoder.transform(labels)
nclasses = len(targetencoder.classes_)

with open(path.join(FEATURES_DATA_DIR, 'targetencoder_rf.pkl'), 'wb') as f:
    pickle.dump(targetencoder, f) # saving the labels to unpack after prediction

X, X_calibration, y, y_calibration = train_test_split(data,
                                      labels,
                                      test_size=0.20,
                                      random_state=0)

parameters = {'max_depth': (3, 4, 5, 6, 7, 8, 9, 10, 11),
              'min_samples_split': (50, 100, 500, 1000),
              'max_features': (30, 50, 100, 150, 200, 300, 500)}

f1_scorer = make_scorer(f1_score, greater_is_better=True, average='weighted')
rfc = RandomForestClassifier(n_estimators=200,  n_jobs=4)
clf = RandomizedSearchCV(rfc, # select  the best hyperparameters
                         parameters,
                         n_jobs=4,
                         n_iter=40,
                         random_state=42,
                         scoring=f1_scorer)

clf.fit(X, y)
clf.best_params_
# calibrating the model
sig_clf = CalibratedClassifierCV(clf.best_estimator_, method='sigmoid', cv='prefit')
sig_clf.fit(X_calibration, y_calibration)

with open(path.join(MODELS_DIR, 'rfc_500.pkl'), 'wb') as f:
    pickle.dump(sig_clf, f)
