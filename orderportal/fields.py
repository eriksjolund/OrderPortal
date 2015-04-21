"OrderPortal: Fields utility class."

from __future__ import unicode_literals, print_function, absolute_import

import logging

import orderportal
from orderportal import constants
from orderportal import settings
from orderportal import utils


class Fields(object):
    "Handle fields in an form or an order."

    def __init__(self, form):
        """Set reference to the form containing the fields,
        and set up lookup."""
        self.form = form
        self.fields = form['fields']
        self.setup()

    def setup(self):
        self._flattened = self._flatten(self.fields)
        self._lookup = dict([(f['identifier'], f)
                             for f in self._flatten(self.fields)])

    def _flatten(self, fields, depth=0):
        result = []
        for field in fields:
            field['depth'] = depth
            result.append(field)
            if field['type'] == constants.GROUP['value']:
                result.extend(self._flatten(field['fields'], depth+1))
        return result

    def __iter__(self):
        return iter(self._flattened)

    def __contains__(self, identifier):
        return identifier in self._lookup

    def __getitem__(self, identifier):
        return self._lookup[identifier]

    def add(self, identifier, rqh):
        "Add a field from HTML form data in the RequestHandler instance."
        assert identifier not in self, 'field identifier must be unique in form'
        type = rqh.get_argument('type')
        assert type in constants.TYPES_SET, 'invalid field type'
        new = dict(identifier=identifier,
                   label=rqh.get_argument('label', None),
                   type=rqh.get_argument('type'),
                   required=utils.to_bool(
                       rqh.get_argument('required', False)),
                   restrict_read=utils.to_bool(
                       rqh.get_argument('restrict_read', False)),
                   restrict_write=utils.to_bool(
                       rqh.get_argument('restrict_write', False)),
                   description=rqh.get_argument('description', None))
        if type == constants.GROUP['value']:
            new['fields'] = []
        group = rqh.get_argument('group', None)
        if group == '__none__': group = None
        for field in self:
            if field['identifier'] == group:
                field['fields'].append(new)
                break
        else:
            self.form['fields'].append(new)
        self.setup()
        return new

    def update(self, identifier, rqh):
        "Update the field from HTML form data in the RequestHandler instance."
        assert identifier in self, 'field identifier must be defined in form'
        new = dict(label=rqh.get_argument('label', None),
                   required=utils.to_bool(
                       rqh.get_argument('required', False)),
                   restrict_read=utils.to_bool(
                       rqh.get_argument('restrict_read', False)),
                   restrict_write=utils.to_bool(
                       rqh.get_argument('restrict_write', False)),
                   description=rqh.get_argument('description', None))
        field = self._lookup[identifier]
        field.update(new)
        return field            # Yes, 'field', not 'new'.

    def delete(self, identifier):
        "Delete the field and its children, if any."
        assert identifier in self, 'field identifier must be defined in form'
        self._delete(self.fields, identifier)
        self.setup()

    def _delete(self, fields, identifier):
        "Search recursively for the field and delete it and its children."
        for i, field in enumerate(fields):
            if field['identifier'] == identifier:
                fields.pop(i)
                logging.debug("deleted %s", identifier)
                return
            if field['type'] == constants.GROUP:
                self._delete(field['fields'], identifier)
