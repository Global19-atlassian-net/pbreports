import logging
import string
import unittest

from jsonschema import ValidationError

from pbcommand.models.report import Attribute, Plot, PlotGroup, Column, Table

from pbreports.model.validators import (validate_attribute, validate_plot,
                                        validate_plot_group, validate_column,
                                        validate_table)

log = logging.getLogger(__name__)


class TestAttributeValidators(unittest.TestCase):
    def test_basic(self):
        a = Attribute('my_id', 12, name="My Attribute")
        d = a.to_dict()
        validate_attribute(d)

    def test_failed_id(self):
        d = {'id': 1234, 'value': 1234, 'name': 'my name'}
        with self.assertRaises(ValidationError) as e:
            validate_attribute(d)
            log.info(e)

    def test_null_name(self):
        d = dict(id='my_id', name=None, value="a value")

        with self.assertRaises(ValidationError) as e:
            validate_attribute(d)
            log.info(e)

    def test_int_id(self):
        d = dict(id=1234, value="a value")
        with self.assertRaises(ValidationError):
            validate_attribute(d)


class TestPlotValidator(unittest.TestCase):
    def test_basic(self):
        image = 'image.png'
        p = Plot('my_id', image, caption="Caption", thumbnail=image)
        d = p.to_dict()
        validate_plot(d)


class TestPlotGroupValidator(unittest.TestCase):
    def test_basic(self):
        p1 = Plot('p1', 'image.png', thumbnail='thumb.png')
        p2 = Plot('p2', 'image2.png', thumbnail='thumb2.png')
        plots = [p1, p2]
        title = "My Plots"
        legend = "Legend"
        thumbnail = p1.thumbnail
        pg = PlotGroup('my_id', title=title, legend=legend,
                       thumbnail=thumbnail, plots=plots)

        d = pg.to_dict()
        validate_plot_group(d)
        self.assertIsNotNone(d)


def _column_generator(id_, values):
    c = Column(id_, header="My Column", values=values)
    return c


class TestColumnValidator(unittest.TestCase):
    def test_basic(self):
        c = _column_generator('my_id', list(xrange(3)))
        d = c.to_dict()
        validate_column(d)
        self.assertIsNotNone(d)


class TestTableValidator(unittest.TestCase):
    def test_basic(self):
        n = 3
        columns = [_column_generator('my_id1', list(xrange(n))),
                   _column_generator('my_id2', string.lowercase[:n])]

        title = "My Table"
        table = Table('my_table', title=title, columns=columns)

        d = table.to_dict()
        validate_table(d)

        self.assertIsNotNone(d)
