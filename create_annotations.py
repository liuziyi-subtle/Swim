from matplotlib.widgets import RectangleSelector
import numpy as np
import matplotlib.pyplot as plt
import json
from glob import glob
import os
import pandas as pd
from datetime import datetime


def str2id(s):
    return int.from_bytes(s.encode('utf-8'), 'little')


def line_select_callback(eclick, erelease):
    'eclick and erelease are the press and release events'
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
    print(" The button you used were: %s %s" %
          (eclick.button, erelease.button))
    return eclick, erelease


def toggle_selector(event):
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print(' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print(' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)
    if event.key in ['E', 'e']:
        start = int(toggle_selector.RS.corners[0][0])
        end = int(toggle_selector.RS.corners[0][2])
        category_name = input('输入标注类别: ')
        category_id = toggle_selector.labelmap[category_name]
        count = input('输入划水次数: ')
        toggle_selector.dict_segment['start'] = toggle_selector.date[start]
        toggle_selector.dict_segment['end'] = toggle_selector.date[end]
        toggle_selector.dict_segment['category_id'] = category_id
        toggle_selector.dict_segment['count'] = int(count)
        toggle_selector.dict_segment['id'] = toggle_selector.dict_segment['record_id'] + str2id(
            toggle_selector.date[start])
        print("x-> 保存!")
    if event.key in ['X', 'x']:
        json_dict = {'record': toggle_selector.dict_record,
                     'segment': toggle_selector.dict_segment}
        json_dict = json.dumps(json_dict)
        print(json_dict)
        json_name = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_name = json_name.replace(' ', '(') + ').json'
        json_path = os.path.join(toggle_selector.save_dir, json_name)
        with open(json_path, 'w') as f:
            f.write(json_dict)


def annotate_segment(record_path, labelmap, save_dir, toggle_selector):
    record = pd.read_csv(record_path)
    value = record['Accelerometer X']
    fig, current_ax = plt.subplots()
    plt.plot(range(value.shape[0]), value)
    # global toggle
    toggle_selector.date = record['Timestamp']
    toggle_selector.labelmap = labelmap
    toggle_selector.save_dir = save_dir
    toggle_selector.dict_record = annotate_record(record_path.split('/')[-1])
    gender = input('输入性别: ')
    toggle_selector.dict_record['gender'] = gender
    toggle_selector.dict_segment = {}
    toggle_selector.dict_segment['record_id'] = toggle_selector.dict_record['id']
    toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,
                                           drawtype='box', useblit=True,
                                           # don't use middle button
                                           button=[1, 3],
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)
    plt.connect('key_press_event', toggle_selector)
    plt.title(record_path.split('/')[-1])
    plt.show()


def annotate_record(record_name):
    return dict({'name': record_name,
                 'id': str2id(record_name),
                 'pool_length': 50})


record_dir = '/Users/liuziyi/Workspace/data/in'
record_paths = glob(os.path.join(record_dir, 'TAS1F*.csv'))
save_dir = '/Users/liuziyi/Workspace/data/out'
with open("/Users/liuziyi/Workspace/data/in/labelmap.json", 'r') as f:
    labelmap = json.load(f)
labelmap = dict([(element['name'], element['id'])
                 for element in labelmap['categories']])
for rp in record_paths:
    print(rp)
    annotate_segment(rp, labelmap, save_dir, toggle_selector)
    finish = input("继续下一个样本: y/n")
