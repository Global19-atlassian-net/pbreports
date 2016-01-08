#!/usr/bin/env python
import argparse
import logging
import os
import sys

import numpy as np

from pbreports.pbsystem_common.cmdline.core import main_runner_default
from pbreports.pbsystem_common.cmdline.validators import validate_file


from pbreports.io.filtered_summary_reader import FilteredSummaryReader
from pbreports.util import movie_to_cell, get_base_parser, add_base_options
from pbreports.model.model import Attribute, Table, Column, Report

log = logging.getLogger(__name__)

__version__ = '2.0'


def make_loading_report(csv, report, output_dir):

    if not os.path.exists(csv):
        raise IOError('File does not exist {f}'.format(f=csv))
#    validate_csv(csv)
    d = {'csv': csv,
         'report': report,
         'output_dir': output_dir}
    log.info("Making loading report with args: " + str(d))

    np_arr = _get_filtered_data(csv)

    table, atts = _get_loading_table_and_attributes(np_arr)

    r = Report('loading',
               attributes=atts,
               tables=[table])
    r.write_json(os.path.join(output_dir, report))

def _get_loading_table_and_attributes(np_arr):

    t = Table('productivity')
    atts = []
    for c in _get_columns():
        t.add_column(c)

    c0, c1,c2,c3,c4 = [],[],[],[], []
    cell_dict = _get_counts_by_cell(np_arr)
    for k, v in cell_dict.iteritems():
        cellid = k
        zmws = np.sum(v.values())
        ratios = [v[p] / float(zmws) for p in _get_productivities()]
        t.append_data(0, cellid)
        t.append_data(1, int(zmws))
        t.append_data(2, ratios[0])
        t.append_data(3, ratios[1])
        t.append_data(4, ratios[2])

    num_cells = len(cell_dict.items())

    ### get loading totals
    table_dict = t.to_dict()
    c1 = (item for item in table_dict['columns'] if item["id"] == "productivity.c1").next()
    productivity_c1 = sum(c1['values'])
    c2 = (item for item in table_dict['columns'] if item["id"] == "productivity.c2").next()
    productivity_c2 = sum(c2['values']) / num_cells
    c3 = (item for item in table_dict['columns'] if item["id"] == "productivity.c3").next()
    productivity_c3 = sum(c3['values']) / num_cells
    c4 = (item for item in table_dict['columns'] if item["id"] == "productivity.c4").next()
    productivity_c4 = sum(c4['values']) / num_cells

    atts.append(Attribute('productivity_c1', productivity_c1, 'Productive ZMWs'))
    atts.append(Attribute('productivity_c2', productivity_c2, 'ZMW Loading Productivity 2'))
    atts.append(Attribute('productivity_c3', productivity_c3, 'ZMW Loading Productivity 3'))
    atts.append(Attribute('productivity_c4', productivity_c4, 'ZMW Loading Productivity 4'))

    return t, atts


def _get_productivities():
    return [0, 1, 2]


def _get_column_labels():
    labels = ['SMRT Cell ID', 'Productive ZMWs']
    labels.extend(['Productivity {p} (%)'.format(p=p) for p in _get_productivities()])
    return labels


def _get_columns():
    """
    Return the list of column objects that get added to the table
    """
    labels = _get_column_labels()
    cs = []
    for i in range(len(labels)):
        c = Column('c{i}'.format(i=i), header=labels[i])
        cs.append(c)
    return cs


def _get_filtered_data(csv):
    """
    Return a numpy array of csv data filtered by
        SequencingZMW > 0 and Productivity != 255

    csv: path to filtered_summary.csv f
    """
    reader = FilteredSummaryReader(csv)
    reader.load()
    data = reader.data_as_numpy_array()
    data = data[data["SequencingZMW"] > 0]
    data = data[data["Productivity"] != 255]
    return data


def _get_counts_by_cell(data):
    """
    Return a dictionary of processed data:
    The key is cell name, the value is a dict - key == int (productivity
    key), value == int (productivity count)
    """
    tuple_list = [(p, 0) for p in _get_productivities()]
    d = {}
    for row in data:
        cell = movie_to_cell(row['Movie'])
        d.setdefault(cell, dict(tuple_list))
        d[cell][row['Productivity']] += 1
    return d


def args_runner(args):
    return make_loading_report(args.csv, args.report, args.output)


def add_options_to_parser(p):
    # Using Johann's supbarser model, the modification state of
    # the parser needs to be a done as a separate operation
    # this is actually a nice model because a parser or subparser
    # can be used.
    p = add_base_options(p)
    p.description = "'Generates a report exposing summary stats for the ' + \
            'Productivity metric from primary.'"
    p.add_argument("csv", help="filtered_summary.csv", type=validate_file)
    p.set_defaults(func=args_runner)
    return p


def get_parser():
    p = argparse.ArgumentParser(version=__version__)
    p = add_options_to_parser(p)
    return p


def main(argv=sys.argv):
    """Main point of Entry"""
    log.info("Starting {f} version {v} report generation".format(f=__file__, v=__version__))
    return main_runner_default(argv[1:], get_parser(), log)
