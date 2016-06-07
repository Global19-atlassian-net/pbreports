#!/usr/bin/env python

import json

from pbcommand.models.report import Attribute, Report


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
        assert type(value).__name__ == self.type, "{v} != {t}".format(
            v=value, t=self.type)
        return Attribute(self.id, value=value, name=self.name)


class MetaReport(object):
    def __init__(self, id_, title, attributes=()):
        self.id = id_
        self.title = title
        self.attributes = attributes
        self._attr_dict = {a.id:a for a in attributes}

    @staticmethod
    def from_json(json_str):
        d = json.loads(json_str)
        return MetaReport(d['id'], d['title'],
                          [MetaAttribute.from_dict(a) for a in d['attributes']])

    def get_meta_attribute(self, id_):
        return self._attr_dict[id_]

    def as_report(self, attributes=(), uuid=None):
        return Report(self.id, self.title, attributes=attributes,
                      uuid=uuid)


def main():
    meta_rpt = MetaReport.from_json("""\
{
    "id" : "test_report",
    "title" : "Example report spec",
    "attributes" : [
        {
            "id": "mapped_read_length",
            "name": "Mapped Polymerase Read Length (mean)",
            "description": "Something useful and verbose",
            "type": "int"
        },
        {
            "id": "concordance",
            "name": "Mean Mapped Concordance",
            "description": "An actual formula could go here",
            "type": "float"
        }
    ]
}""")
    rpt = meta_rpt.as_report(attributes=[
        meta_rpt.get_meta_attribute("mapped_read_length").as_attribute(10000),
        meta_rpt.get_meta_attribute("concordance").as_attribute(0.85)
    ])
    print rpt.to_json()


if __name__ == "__main__":
    main()
