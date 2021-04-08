"""
Copyright (c) 2018 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import re
import json

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckanext.edsmetadata.helpers as _h

from ckan.lib.plugins import DefaultTranslation
from ckan.lib.plugins import DefaultDatasetForm

from ckanext.edsmetadata.logic.action.update import (package_update, resource_update)
from ckanext.edsmetadata.logic.action.create import resource_create
from ckanext.edsmetadata.logic.action.get import package_show

log = logging.getLogger(__name__)


class EDSMetadataPlugin(p.SingletonPlugin, DefaultDatasetForm, DefaultTranslation):
    p.implements(p.ITranslation)
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    p.implements(p.IActions)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.ITemplateHelpers)

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'str_to_dict': str_to_dict,
            'resource_excluded_fields': lambda: toolkit.aslist(
                config.get('ckanext.edsmetadata.resource_excluded_fields',
                           'attributes filters format ')),
            'split_string': lambda text, delim: text.split(delim),
            'markdown_fields': _h.markdown_fields
        }

    # IRoutes

    def before_map(self, map):
        ctrl = 'ckanext.edsmetadata.controller:EdsMetadataController'
        map.connect('resource_edit',
                    '/dataset/{id}/resource_edit/{resource_id}',
                    controller=ctrl, ckan_icon='edit',
                    action='resource_edit')
        map.connect('new_resource',
                    '/dataset/new_resource/{id}',
                    controller=ctrl, ckan_icon='add',
                    action='new_resource')
        return map

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'edsmetadata')

    def get_actions(self):
        return {
            'package_update': package_update,
            'package_show': package_show,
            'resource_create': resource_create,
            'resource_update': resource_update
        }

    # IDatasetForm

    def _modify_package_schema(self, schema):
        defaults = [toolkit.get_validator('ignore_missing'), toolkit.get_converter('convert_to_extras')]
        not_empty = [toolkit.get_validator('not_empty'),
                     toolkit.get_converter('convert_to_extras')]

        schema.update({
            'notes': not_empty,
            'comment': defaults,
            'resolution': not_empty,
            'related-datasets': defaults,
            'metadata_language': defaults,
            'update_frequency': not_empty,
            'author': not_empty,
            'author_email': [toolkit.get_validator('not_empty'),
                             toolkit.get_converter('convert_to_extras'), _validate_email]

        })
        schema['resources'].update({
            'attributes': defaults
        })

        return schema

    def create_package_schema(self):
        schema = super(EDSMetadataPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)

        return schema

    def update_package_schema(self):
        schema = super(EDSMetadataPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)

        return schema

    def show_package_schema(self):
        schema = super(EDSMetadataPlugin, self).show_package_schema()
        defaults = [toolkit.get_converter('convert_from_extras'),
                    toolkit.get_validator('ignore_missing')]

        schema.update({
            'notes': defaults,
            'comment': defaults,
            'resolution': defaults,
            'metadata_language': defaults,
            'update_frequency': defaults,
            'author': defaults,
            'author_email': [toolkit.get_validator('not_empty'),
                             toolkit.get_converter('convert_from_extras'),
                             _validate_email],
            'related-datasets': defaults

        })
        schema['resources'].update({
            'attributes': defaults,
        })

        return schema

    def is_fallback(self):
        return True

    def package_types(self):
        return []


def _validate_email(key, data, errors, context):
    regex = config.get(
        'ckanext.edsmetadata.email_regex',
        '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    )
    email = data.get(key)
    match = re.match(regex, email)
    if match is None:
        errors[key].append('You must provide valid e-mail address!')


def str_to_dict(text):
    _ = {}
    try:
        _ = json.loads(text)
    except Exception as e:
        pass
    return _

