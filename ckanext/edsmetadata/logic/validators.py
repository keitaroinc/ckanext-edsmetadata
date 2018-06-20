import logging
import json

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

from ckan.common import _ as _trans

log = logging.getLogger(__name__)

from ckanext.edsmetadata.helpers import _get_required_attrs, _get_optional_attrs


def validate_resource_attributes_list(attributes):
    errors = {}
    while isinstance(attributes, (unicode, basestring)):
        attributes = json.loads(attributes)

    for attribute in attributes:
        attr_keys, required_keys = set(attribute.keys()), set(_get_required_attrs())
        missing = required_keys.difference(attr_keys)

        if any(missing):
            map(lambda k: errors.update({k: [_trans('Missing value')]}), missing)

        for required_key in required_keys:
            if attribute[required_key] in ('', u'', None):
                errors.update({required_key: [_trans('Missing value')]})

        for key, val in attribute.items():
            if key.startswith('type'):
                if val.lower() in ('int', 'integer', 'float', 'decimal'):
                    # Process conditional fields
                    for cond_attr in ['unit']:
                        if cond_attr in attribute:
                            if attribute[cond_attr] in (None, '', u''):
                                errors.update({cond_attr: [_trans('Missing value')]})
                        else:
                            errors.update({cond_attr: [_trans('Missing value')]})

    return errors
