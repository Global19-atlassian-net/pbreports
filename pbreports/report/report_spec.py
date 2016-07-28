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
        #        assert type(value).__name__ == self.type, "{v} != {t}".format(v=type(value), t=self.type)
        return Attribute(self.id, value=value, name=self.name)
   
    def apply_attribute_view(self, attr):
    	if (attr.name is None) or (not attr.name):
    		name = self.name
    	else:
    		name = attr.name
    	return Attribute(self.id, value=attr.value, name=name)

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
        #	for value in values:
        #		assert type(value).__name__ == self.type, "{v} != {t}".format(v=type(value), t=self.type)
        return Column(self.id, header=self.header, values=values)

    def apply_column_view(self, col):
        if (col.header is None) or (not col.header):
                header = self.header
        else:
                header = col.header
        return Column(self.id, values=col.values, header=header)


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

    def apply_table_view(self, table):
        if table.title is None:
                title = self.title
        else:
                title = table.title
        return Table(self.id, title=title, columns=[self.get_meta_column(c.id).apply_column_view(c) for c in table.columns])


class MetaPlot(object):

    def __init__(self, id_, description, caption, title, xlabel, ylabel):
        self.id = id_
        self.description = description
        self.caption = caption
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

    @staticmethod
    def from_dict(d):
        return MetaPlot(d['id'].split(".")[-1], d['description'], d['caption'], d['title'], d['xlabel'], d['ylabel'])

    def as_plot(self, image, thumbnail):
        return Plot(self.id, image=image, caption=self.caption, title=self.title, thumbnail=thumbnail)

    def apply_plot_view(self, plot):
    	caption = plot.caption
   	title = plot.title
        if caption is None:
                caption = self.caption
    	if title is None:
                title = self.title
    	return Plot(self.id, image=plot.image, caption=caption, title=title, thumbnail=plot.thumbnail)


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

    def apply_plotgroup_view(self, plotgroup):
        legend = plotgroup.legend
        title = plotgroup.title
        if legend is None:
                legend = self.legend
        if title is None:
                title = self.title
        return PlotGroup(self.id, title=title, legend=legend, thumbnail=plotgroup.thumbnail, plots=[self.get_meta_plot(p.id).apply_plot_view(p) for p in plotgroup.plots])


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
                          [MetaAttribute.from_dict(a)
                           for a in d['attributes']],
                          [MetaPlotGroup.from_dict(p)
                           for p in d['plotgroups']],
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

    def apply_view(self, report):
    	return Report(self.id, self.title, 
                      attributes=[self.get_meta_attribute(a.id).apply_attribute_view(a) for a in report.attributes],
                      tables=[self.get_meta_table(t.id).apply_table_view(t) for t in report.tables],
#                      plotgroups=[self.get_meta_plotgroup(p.id).apply_plotgroup_view(p) for p in report.plotGroups],
    		      plotgroups=report.plotGroups,
                      dataset_uuids=report.dataset_uuids, uuid=report.uuid)

