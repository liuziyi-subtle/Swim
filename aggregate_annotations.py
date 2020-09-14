'''Aggregate json annotations into an integrated json file.
'''
from glob import glob
import json
import pandas as pd


def set_dict(dict_list):
    ''' return a list containing unique dicts
    '''
    unique_dicts = []
    for d in dict_list:
        if d not in unique_dicts:
            unique_dicts.append(d)
        else:
            continue
    return unique_dicts


def rename_segment_id(segment_annotation):
    ''' reassign simple id to segment_annotation
    '''
    segment_annotation['id'] = next(rename_segment_id.ITER)


if __name__ == '__main__':
    '''
    usage:
    python3 aggregate_annotations.py --json_dir /data/workspace/data/jsons \
                                     --record_field record \
                                     --segment_field segment \
                                     --labelmap_path /data/workspace/data/labelmap.json \
                                     --save_path /data/workspace/data/annotations.json
    '''
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_dir', type=str, help='')
    parser.add_argument('--record_field', type=str, help='')
    parser.add_argument('--segment_field', type=str, help='')
    parser.add_argument('--labelmap_path', type=str, help='')
    parser.add_argument('--save_path', type=str, help='')

    args = parser.parse_args()
    json_paths = glob(os.path.join(args.json_dir, '*.json'))
    record_annotations = []
    segment_annotations = []
    category_annotations = []
    rename_segment_id.ITER = iter(range(1000000))
    for jp in json_paths:
        with open(jp, 'r') as f:
            annotation = json.load(f)
            record_annotations.append(annotation[args.record_field])
            rename_segment_id(annotation[args.segment_field])
            segment_annotations.append(annotation[args.segment_field])
    record_annotations = set_dict(record_annotations)

    with open(args.labelmap_path, 'r') as f:
        category_annotations = json.load(f)

    annotations = {'record_annotations': record_annotations,
                   'segment_annotations': segment_annotations,
                   'category_annotations': category_annotations['categories']}
    annotations = json.dumps(annotations)
    with open(args.save_path, 'w') as f:
        f.write(annotations)
        print("Done.")
