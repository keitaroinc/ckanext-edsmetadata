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
