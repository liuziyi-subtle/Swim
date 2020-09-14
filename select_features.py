from sklearn import pipeline
import numpy as np


class FeatureSelection():
    def __init__(self, pipeline=None):
        self.pipeline = pipeline

    def fit(self, X_train, y_train):
        self.pipeline.fit(X_train, y_train)

    def score(self, X_test, y_test):
        return self.pipeline.score(X_test, y_test)

    def get_selected_features(self, feature_columns=None,
                              feature_selector_index=None):
        assert feature_selector_index, 'must specify index of feature selector'
        assert feature_columns, 'feature_columns is none'

        feature_column_index = self.pipeline[int(feature_selector_index)].get_selected_features(
        )
        print(feature_column_index, type(feature_column_index))
        return np.array(feature_columns)[feature_column_index]
