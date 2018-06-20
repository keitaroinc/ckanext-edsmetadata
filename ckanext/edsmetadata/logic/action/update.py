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
