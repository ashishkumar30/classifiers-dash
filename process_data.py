import pandas as pd
import numpy as np
from itertools import combinations
#from visualizers import classification_report, rocauc, pr_curve, confusion_matrix
from visualizers2 import Visualizer
from helpers import evaluate_model, save_report
from upsample import upsample
from load_data import load_data
from sklearn.model_selection import train_test_split
from pandas.io.json import json_normalize

from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.utils import resample


def create_report_df(upsampled=False):

    models = [GradientBoostingClassifier(), RandomForestClassifier(), LogisticRegression(), GaussianNB() ]
    visualizers = ['ClassificationReport', 'ROCAUC','PrecisionRecallCurve', 'ConfusionMatrix']

    df, labels, X, y = load_data()
    train_df, test_df = train_test_split(df, test_size = .30, random_state=42)

    if upsampled==True:
        df_upsampled, X_train, y_train= upsample(train_df, 'purchase', labels)
        X_test = test_df[labels].values
        y_test = test_df['purchase'].values

    else:
        X_train = train_df[labels].values
        y_train = train_df['purchase'].values
        X_test = test_df[labels].values
        y_test = test_df['purchase'].values

    report_dict= {}
    for model_ in models:
        for visualizer_ in visualizers:
            viz = Visualizer(X, y, labels, model_, visualizer_, upsampled=upsampled)
            viz.evaluate()
            viz.save_img()

        model = model_
        model.fit(X_train, y_train)
        report_dict[str(model).split('(')[0]] = evaluate_model(model, X_test, y_test)

    report_df = pd.DataFrame.from_dict(report_dict).T

    if report_df.columns.tolist() == ['0', '1', 'accuracy', 'macro avg', 'weighted avg']:
        pass
    else:
        print("Warning: Column names aren't as expected. Verify report_df output_dict is correct.")
    report_df.columns = ['0', '1', 'accuracy', 'Macro Avg', 'Micro Avg' ]


    dict_columns = ['0', '1', 'Macro Avg', 'Micro Avg']
    keys = ['precision', 'recall', 'f1-score', 'support']

    def revise_dict(x, col, keys):
        new_keys = [key+'_'+col for key in keys]
        new_dict = dict(zip(new_keys, list(x.values())))
        return new_dict

    for col in dict_columns:
        report_df[col] = report_df[col].apply(lambda x: revise_dict(x, col, keys))

    for col in dict_columns:
        new_dict = {}
        for classifier in report_df.index.values.tolist():
            name = str(classifier) + '_df'
            new_dict[name]= json_normalize(report_df.loc[classifier][col])
            new_dict[name]['classifier'] = [classifier]
        dict_df = pd.concat(list(new_dict.values())).reset_index().drop(columns=['index'], axis=1)

        report_df = report_df.merge(dict_df, how='left', left_index=True, left_on=None, right_on='classifier').set_index('classifier')

    report_df = report_df.iloc[:,5:]
    report_df = report_df[sorted([col for col in report_df.columns if 'support' not in col])]

    return report_df

report_df = create_report_df()
report_df.to_csv('Data/Output/report_df.csv')

report_df_upsampled = create_report_df(upsampled=True)
report_df_upsampled.to_csv('Data/Output/report_df_upsampled.csv')
