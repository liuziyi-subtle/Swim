from tsfresh.examples.har_dataset import download_har_dataset, load_har_dataset, load_har_classes
import seaborn as sns
from tsfresh import extract_features, extract_relevant_features, select_features
from tsfresh.utilities.dataframe_functions import impute
from tsfresh.feature_extraction import ComprehensiveFCParameters
import pandas as pd
import numpy as np


def tsfresh_featurs(df_objects, cols2extract):
    '''extract tsfresh features
    '''
    extraction_settings = ComprehensiveFCParameters()
    ids = df_objects['id'].unique()
    df_features = []
    for c in cols2extract:
        df = df_objects.loc[:, ['id', c]].copy()
        X = extract_features(df, column_id='id', impute_function=impute,
                             default_fc_parameters=extraction_settings)
        df_features.append(X)
    df_features = pd.concat(df_features, axis=1)
    df_features['category'] = list(
        map(lambda x: df_objects[df_objects['id'] == x]['category'].values[0], ids))
    df_features['segment_id'] = list(
        map(lambda x: df_objects[df_objects['id'] == x]['segment_id'].values[0], ids))
    return df_features


def make_pairs(elements):
    pairs = []
    for i in range(1, len(elements)):
        pairs.extend(list(zip(elements[i:], elements[:-i])))
    return pairs


def angle_feature(df_objects, cols2extract):
    def cosine(a, b):
        cos_angle = np.dot(a, b) / (np.sqrt(np.dot(a, a))
                                    * np.sqrt(np.dot(b, b)))
        return np.arccos(cos_angle)
    print(cols2extract)
    assert len(cols2extract) > 1, 'num of cols2extract < 2.'
    assert 'id' in df_objects, 'id missing.'

    pairs = make_pairs(cols2extract)
    cos_angle_list = []
    for name, group in df_objects.groupby('id'):
        cos_angles = [cosine(group[x], group[y]) for x, y in pairs]
        cos_angle_list.append(cos_angles)
    return pd.DataFrame(cos_angle_list, columns=[str(x) + '/' + str(y) for x, y in pairs])


if __name__ == '__main__':
    '''
    usage:
    python3 ./extract_features.py --object_path /data/workspace/data/objects.csv \
                                  --feature_path /data/workspace/data/features.csv
    python3 ./extract_features.py --object_path /data/workspace/data/objects_25hz.csv \
                                  --feature_path /data/workspace/data/features_25hz.csv    
    '''
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--object_path', type=str, help='')
    parser.add_argument('--feature_path', type=str, help='')
    args = parser.parse_args()

    df_objects = pd.read_csv(args.object_path)
    # df_objects = df_objects[df_objects['id'] < 50]
    object_columns = list(df_objects.columns)

    cols2tsfresh = set(object_columns) ^ set(
        ['Unnamed: 0', 'Timestamp', 'category', 'segment_id', 'id'])
    df_tsfresh_featurs = tsfresh_featurs(df_objects, cols2tsfresh)  # tsfresh特征

    cols2angle = ['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']
    df_angle_features = angle_feature(df_objects, cols2angle)

    # cos2angle_body = ['BodyAccelerometer X',
    #                   'BodyAccelerometer Y', 'BodyAccelerometer Z']
    # df_angle_features_body = angle_feature(df_objects, cos2angle_body)

    df_features = pd.concat(
        [df_tsfresh_featurs, df_angle_features], axis=1)
    df_features.to_csv(args.feature_path)
    print('Done.')
