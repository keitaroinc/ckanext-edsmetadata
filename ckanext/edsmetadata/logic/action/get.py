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
import json
import logging

import ckan.logic as l
import ckanext.edsmetadata.helpers as h

from ckan.plugins import toolkit

log = logging.getLogger(__name__)

@toolkit.side_effect_free
def package_show(context, data_dict):
    out = l.action.get.package_show(context, data_dict)
    if 'resources' in out and any(out['resources']):
        resources = out.pop('resources')
        for res in resources:
            if 'attributes' in res:
                if isinstance(res['attributes'], (unicode, basestring)):
                    attrs = res.pop('attributes')
                    res['attributes'] = json.loads(attrs)
                else:
                    res['attributes'] = json.loads(h._resource_extra_obj(res['id'], key='attributes'))
            else:
                res['attributes'] = json.loads(h._resource_extra_obj(res['id'], key='attributes'))

            if 'filters' in res:
                if isinstance(res['filters'], (unicode, basestring)):
                    filters = res.pop('filters')
                    res['filters'] = json.loads(filters)
                else:
                    res['filters'] = json.loads(h._resource_extra_obj(res['id'], key='filters'))
            else:
                res['filters'] = json.loads(h._resource_extra_obj(res['id'], key='filters'))

        out['resources'] = resources
    return out

