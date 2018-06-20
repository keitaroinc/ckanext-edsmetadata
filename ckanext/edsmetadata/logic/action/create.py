# -*- coding: utf-8 -
import logging
import ckan.logic as l
from ckanext.edsmetadata.logic.validators import validate_resource_attributes_list

log = logging.getLogger(__name__)


def resource_create(context, data_dict):
    attributes = data_dict.pop('attributes', [])
    errors = validate_resource_attributes_list(attributes)

    if any(errors):
        raise l.ValidationError(errors)

    data_dict['attributes'] = attributes
    return l.action.create.resource_create(context, data_dict)
