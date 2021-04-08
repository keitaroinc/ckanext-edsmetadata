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
from ckanext.edsmetadata.logic.validators import validate_resource_attributes_list

log = logging.getLogger(__name__)


def resource_create(context, data_dict):
    attributes = data_dict.pop('attributes', [])
    errors = validate_resource_attributes_list(attributes)

    if any(errors):
        raise l.ValidationError(errors)

    data_dict['attributes'] = attributes
    return l.action.create.resource_create(context, data_dict)

