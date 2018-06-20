import logging

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import ckan.plugins.toolkit as t
import ckan.model as m

from ckan.common import _ as _trans

log = logging.getLogger(__name__)

markdown_fields = lambda: t.aslist(
    config.get('ckanext.edsmetadata.markdown_fields',
               'comment attribute_description')
)


def _resource_extra_obj(resource_id, key, default='[]'):
    r = m.Resource.get(resource_id)
    if r is None:
        return default

    if key in r.extras:
        return r.extras[key]

    return default


def _get_required_attrs(fields=None):
    if fields is None:
        fields = t.aslist(config.get('ckanext.edsmetadata.resource_required_attr_fields',
                                     ['name_of_attribute', 'name_of_field', 'attribute_description',
                                      'example', 'size', 'type']))
    return fields


def _get_optional_attrs(fields=None):
    if fields is None:
        fields = t.aslist(config.get('ckanext.edsmetadata.resource_optional_attr_fields',
                                     ['validation_rules', 'property_constraint', 'comment',
                                      'format_regex']))
    return fields


def _get_attribute_suffix(text):
    return int(text.split('_')[-1])


def _process_resource_attributes_list(resource_dict):
    attrs, processed = {}, []
    errors = {}
    for key, val in resource_dict.items():
        required_attrs = _get_required_attrs()
        if True in map(lambda a: key.startswith(a), required_attrs):
            suffix = _get_attribute_suffix(key)
            if suffix in processed:
                continue

            # Found required key - process all fields for this attr
            _ = {'_'.join(key.split('_')[:-1]): val}
            if val in (None, '', u''):
                errors.update({key: [_trans('Missing value')]})

            if key.startswith('type'):
                # Process conditional fields
                for cond_attr in ['unit']:
                    if '{0}_{1}'.format(cond_attr, suffix) in resource_dict:
                        _.update({cond_attr: resource_dict['{0}_{1}'.format(cond_attr, suffix)]})
                        if val.lower() in ('int', 'integer', 'float', 'decimal'):
                            if resource_dict['{0}_{1}'.format(cond_attr, suffix)] in (None, '', u''):
                                errors.update({'{0}_{1}'.format(cond_attr, suffix): [_trans('Missing value')]})
                        resource_dict.pop('{0}_{1}'.format(cond_attr, suffix))

            resource_dict.pop(key)
            required_attrs.remove('_'.join(key.split('_')[:-1]))

            # Process remaining required fields
            for attr in required_attrs:
                if '{0}_{1}'.format(attr, suffix) in resource_dict:
                    _.update({attr: resource_dict['{0}_{1}'.format(attr, suffix)]})
                    if attr == 'type':
                        # Process conditional fields
                        for cond_attr in ['unit']:
                            if '{0}_{1}'.format(cond_attr, suffix) in resource_dict:
                                _.update({cond_attr: resource_dict['{0}_{1}'.format(cond_attr, suffix)]})
                                if resource_dict['{0}_{1}'.format(attr, suffix)].lower() in (
                                        'int', 'integer', 'float', 'decimal'):
                                    if resource_dict['{0}_{1}'.format(cond_attr, suffix)] in (None, '', u''):
                                        errors.update({'{0}_{1}'.format(cond_attr, suffix): [_trans('Missing value')]})
                                resource_dict.pop('{0}_{1}'.format(cond_attr, suffix))

                    if resource_dict['{0}_{1}'.format(attr, suffix)] in (None, ''):
                        errors.update({'{0}_{1}'.format(attr, suffix): [_trans('Missing value')]})
                    resource_dict.pop('{0}_{1}'.format(attr, suffix))

            # Process optional fields
            for attr in _get_optional_attrs():
                if '{0}_{1}'.format(attr, suffix) in resource_dict:
                    _.update({attr: resource_dict['{0}_{1}'.format(attr, suffix)]})
                    resource_dict.pop('{0}_{1}'.format(attr, suffix))

            attrs.update({suffix: _})
            processed.append(suffix)

    res = []
    for key in sorted(attrs):
        res.append(attrs[key])

    return res, errors
