import numpy as np
import os
import json
import pandas as pd
from datetime import datetime
import time
from scipy import signal


object_id_iter = iter(range(10000000))


def resample(record):
    n_sample = int(record.shape[0] / 4)
    record = record.iloc[::4, :]
    return record


def split_body_gravity(record):
    sos = signal.butter(4, 0.25, 'high', fs=100, output='sos')

    record['BodyAccelerometer X'] = signal.sosfilt(
        sos, record['Accelerometer X'])
    record['BodyAccelerometer Y'] = signal.sosfilt(
        sos, record['Accelerometer Y'])
    record['BodyAccelerometer Z'] = signal.sosfilt(
        sos, record['Accelerometer Z'])

    return record


preprocess_func_map = {'resample': resample,
                       'split_body_gravity': split_body_gravity}


def local2utc(localtime):
    localtime = datetime.strptime(localtime, "%Y-%m-%d %H:%M:%S")
    utc = time.mktime(localtime.timetuple())
    return utc


def parse_annotation(groundtruth_data):
    annotation_index = {}
    # record_id: segment键值对
    for segment in groundtruth_data['segment_annotations']:
        record_id = segment['record_id']
        if record_id not in annotation_index:
            annotation_index[record_id] = []
        annotation_index[record_id].append(segment)
    # 如果record_id不存在，则从字典删除这条record_id
    for record in groundtruth_data['record_annotations']:
        if record['id'] not in annotation_index:
            annotation_index.pop(record['record_id'])
    return annotation_index


def replace_timestamp(timestamp):
    return timestamp.replace('T', ' ').split('.')[0]


def segment2object(segment, object_length):
    objects = []
    for i in range(0, segment.shape[0] - object_length, int(object_length / 2)):
        object = segment.iloc[i:i+object_length, :].copy()
        object.rename(columns={'id': 'segment_id'}, inplace=True)
        object['id'] = next(object_id_iter)
        objects.append(object)
    return objects


def create_object(record_annotation, annotation_list, record_dir,
                  category_annotations, object_length=256,
                  preprocess_func_s=None):
    file_name = record_annotation['name']
    record = pd.read_csv(os.path.join(record_dir, file_name))

    if preprocess_func_s:
        for pfs in preprocess_func_s.split(','):
            record = preprocess_func_map[preprocess_func_s](record)

    record['Timestamp'] = record['Timestamp'].apply(
        lambda x: replace_timestamp(x))
    record['Timestamp'] = record['Timestamp'].apply(lambda x: local2utc(x))

    object_list = []
    for segment_annotation in annotation_list:
        start = local2utc(replace_timestamp(segment_annotation['start']))
        end = local2utc(replace_timestamp(segment_annotation['end']))
        start_index = int(np.asarray(
            record['Timestamp'] > start).nonzero()[0][0])
        end_index = int(np.asarray(
            record['Timestamp'] < end).nonzero()[0][-1])
        segment = record.iloc[start_index:end_index, :].copy()
        segment['category'] = segment_annotation['category_id']
        segment['id'] = segment_annotation['id']
        objects = segment2object(segment, object_length)
        object_list.extend(objects)
    return object_list


if __name__ == '__main__':
    '''
    usage:
    python3 ./create_dataset.py --annotation_path /data/workspace/data/annotations.json \
                                --record_dir /data/workspace/data/records \
                                --save_path /data/workspace/data/objects.csv
    python3 ./create_dataset.py --annotation_path /data/workspace/data/annotations.json \
                                --record_dir /data/workspace/data/records \
                                --preprocess_func_s split_body_gravity \
                                --save_path /data/workspace/data/objects.csv
    python3 ./create_dataset.py --annotation_path /data/workspace/data/annotations.json \
                                --record_dir /data/workspace/data/records \
                                --preprocess_func_s resample,split_body_gravity \
                                --object_length 64
                                --save_path /data/workspace/data/objects.csv
    python3 ./create_dataset.py --annotation_path /data/workspace/data/annotations.json \
                            --record_dir /data/workspace/data/records \
                            --preprocess_func_s resample \
                            --object_length 64 \
                            --save_path /data/workspace/data/objects_25hz.csv
    '''
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation_path', type=str, help='')
    parser.add_argument('--record_dir', type=str, help='')
    parser.add_argument('--object_length', type=int, default=256, help='')
    parser.add_argument('--preprocess_func_s', type=str, default=None, help='')
    parser.add_argument('--save_path', type=str, help='')
    args = parser.parse_args()

    with open(args.annotation_path, 'r') as f:
        groundtruth = json.load(f)

    annotation_index = parse_annotation(groundtruth)
    record_annotations = groundtruth['record_annotations']
    category_annotations = groundtruth['category_annotations']

    object_list = []
    for record_annotation in record_annotations:
        annotation_list = annotation_index[record_annotation['id']]
        objects = create_object(
            record_annotation, annotation_list, args.record_dir,
            category_annotations, object_length=args.object_length,
            preprocess_func_s=args.preprocess_func_s)
        object_list.extend(objects)
    df_objects = pd.concat(object_list)
    df_objects.to_csv(args.save_path)
    print("Done.")
