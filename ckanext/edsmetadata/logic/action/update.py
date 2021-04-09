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

# -*- coding: utf-8 -
import logging
import ckan.logic as l
import json
from ckanext.edsmetadata.logic.validators import validate_resource_attributes_list

import ckanext.edsmetadata.helpers as h

log = logging.getLogger(__name__)


def package_update(context, data_dict):
    # Override package_update action to ensure
    # that all necessary relations are created
    # when creating datasets using the UI
    data_dict = l.get_action('datasetrelations_package_update')(context, data_dict)

    if 'resources' in data_dict and any(data_dict['resources']):
        resources = data_dict.pop('resources')
        for res in resources:
            if 'filters' in res:
                if isinstance(res['filters'], list):
                    res['filters'] = json.dumps(res['filters'])
            elif 'filters' not in res and 'id' in res:
                res['filters'] = h._resource_extra_obj(res['id'], key='filters')
            else:
                res['filters'] = '[]'

            if 'attributes' in res:
                if isinstance(res['attributes'], list):
                    res['attributes'] = json.dumps(res['attributes'])
                elif isinstance(res['attributes'], basestring):
                    pass
                else:
                    res['attributes'] = json.dumps([])
            else:
                res['attributes'] = json.dumps([])
        data_dict['resources'] = resources

    return l.action.update.package_update(context, data_dict)


def resource_update(context, data_dict):
    attributes = data_dict.pop('attributes', [])
    errors = validate_resource_attributes_list(attributes)

    if any(errors):
        raise l.ValidationError(errors)

    data_dict['attributes'] = attributes
    return l.action.update.resource_update(context, data_dict)

