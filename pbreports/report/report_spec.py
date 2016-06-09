#!/usr/bin/env python

import json

from pbcommand.models.report import Attribute, PlotGroup, Plot, Table, Column, Report


class MetaAttribute(object):

    def __init__(self, id_, name, description, type_):
        self.id = id_
        self.name = name
        self.description = description
        self.type = type_

    @staticmethod
    def from_dict(d):
        return MetaAttribute(d['id'].split(".")[-1], d['name'],
                             d['description'], d["type"])

    def as_attribute(self, value):
        assert type(value).__name__ == self.type, "{v} != {t}".format(v=value, t=self.type)
        return Attribute(self.id, value=value, name=self.name)


class MetaColumn(object):

    def __init__(self, id_, header, description, type_):
        self.id = id_
        self.header = header
        self.description = description
        self.type = type_

    @staticmethod
    def from_dict(d):
        return MetaColumn(d['id'].split(".")[-1], d['header'],
                          d['description'], d["type"])

    def as_column(self, values=()):
	for value in values:
		assert type(value).__name__ == self.type, "{v} != {t}".format(v=value, t=self.type)
        return Column(self.id, header=self.header, values=values)


class MetaTable(object):

    def __init__(self, id_, title, description, columns):
        self.id = id_
        self.title = title
        self.description = description
        self.columns = columns
        self._col_dict = {c.id: c for c in columns}

    @staticmethod
    def from_dict(d):
        return MetaTable(d['id'].split(".")[-1], d['title'],
                         d['description'], [MetaColumn.from_dict(c) for c in d['columns']])

    def get_meta_column(self, id_):
        return self._col_dict[id_]

    def as_table(self, columns=()):
        return Table(self.id, title=self.title, columns=columns)


class MetaPlot(object):

    def __init__(self, id_, description, caption, xlab, ylab):
        self.id = id_
        self.description = description
        self.caption = caption
        self.xlab = xlab
        self.ylab = ylab

    @staticmethod
    def from_dict(d):
        return MetaPlot(d['id'].split(".")[-1], d['description'], d['caption'], d['xlab'], d['ylab'])

    def as_plot(self, image, thumbnail):
        return Plot(self.id, image=image, caption=self.caption, thumbnail=thumbnail)


class MetaPlotGroup(object):

    def __init__(self, id_, title, description, legend, plots=()):
        self.id = id_
        self.title = title
        self.description = description
        self.legend = legend
        self.plots = plots
        self._plot_dict = {p.id: p for p in plots}

    @staticmethod
    def from_dict(d):
        return MetaPlotGroup(d['id'].split(".")[-1], d['title'], d["description"],
                             d['legend'], [MetaPlot.from_dict(p) for p in d['plots']])

    def get_meta_plot(self, id_):
        return self._plot_dict[id_]

    def as_plotgroup(self, thumbnail, plots=()):
        return PlotGroup(self.id, title=self.title, legend=self.legend, thumbnail=thumbnail, plots=plots)


class MetaReport(object):

    def __init__(self, id_, title, description, attributes=(), plotgroups=(), tables=()):
        self.id = id_
        self.title = title
	self.description = description
        self.attributes = attributes
        self.plotgroups = plotgroups
        self.tables = tables
        self._attr_dict = {a.id: a for a in attributes}
        self._plotgrp_dict = {p.id: p for p in plotgroups}
        self._table_dict = {t.id: t for t in tables}

    @staticmethod
    def from_json(json_str):
        d = json.load(open(json_str))
        json.dumps(d)
        return MetaReport(d['id'], d['title'], d['description'],
                          [MetaAttribute.from_dict(a) for a in d['attributes']],
                          [MetaPlotGroup.from_dict(p) for p in d['plotgroups']],
                          [MetaTable.from_dict(t) for t in d['tables']])

    def get_meta_attribute(self, id_):
        return self._attr_dict[id_]

    def get_meta_plotgroup(self, id_):
        return self._plotgrp_dict[id_]

    def get_meta_table(self, id_):
        return self._table_dict[id_]

    def as_report(self, attributes=(), plotgroups=(), tables=(), uuid=None):
        return Report(self.id, self.title, attributes=attributes,
                      plotgroups=plotgroups, tables=tables, uuid=uuid)
