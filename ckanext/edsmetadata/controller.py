import logging
import cgi
from logging import getLogger

from ckan.common import OrderedDict, _, json, request, c, g, response
from ckan.controllers.package import (PackageController,
                                      url_with_params,
                                      _encode_params)

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as l
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.render

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

from ckanext.edsmetadata.helpers import _process_resource_attributes_list

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = l.NotFound
NotAuthorized = l.NotAuthorized
ValidationError = l.ValidationError
check_access = l.check_access
get_action = l.get_action
tuplize_dict = l.tuplize_dict
clean_dict = l.clean_dict
parse_params = l.parse_params
flatten_to_string_key = l.flatten_to_string_key

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

log = getLogger(__name__)


class EdsMetadataController(PackageController):
    def _get_ctx(self):
        return {
            'model': model, 'session': model.Session,
            'user': c.user, 'auth_user_obj': c.userobj,
            'save': 'save' in request.params
        }

    def resource_edit(self, id, resource_id, data=None, errors=None,
                      error_summary=None):

        attr_errors = {}
        if request.method == 'POST' and not data:
            data = data or \
                   clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                       request.POST))))

            if 'filters' in model.Resource.get(resource_id).extras:
                # Include resource filters in the update
                data['filters'] = model.Resource.get(resource_id).extras['filters']

            data['attributes'], attr_errors = _process_resource_attributes_list(data)

            # we don't want to include save as it is part of the form
            del data['save']
            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': c.user, 'auth_user_obj': c.userobj}

            if any(attr_errors):
                errors = attr_errors
                error_summary = {}
                for key, val in errors.items():
                    error_summary.update({key: ' '.join(val)})
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                errors.update(attr_errors)
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except NotAuthorized:
                abort(403, _('Unauthorized to edit this resource'))
            ctrl = 'ckanext.dataextractor.controllers.dataextractor:DataextractorController'
            redirect(h.url_for(controller=ctrl, action='resource_extractor_show',
                               id=id, resource_id=resource_id))

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': c.user, 'auth_user_obj': c.userobj}
        pkg_dict = get_action('package_show')(context, {'id': id})
        if pkg_dict['state'].startswith('draft'):
            # dataset has not yet been fully created
            resource_dict = get_action('resource_show')(context,
                                                        {'id': resource_id})
            return self.new_resource(id, data=resource_dict)
        # resource is fully created
        try:
            resource_dict = get_action('resource_show')(context,
                                                        {'id': resource_id})
        except NotFound:
            abort(404, _('Resource not found'))

        c.pkg_dict = pkg_dict
        c.resource = resource_dict
        # set the form action
        c.form_action = h.url_for(controller='package',
                                  action='resource_edit',
                                  resource_id=resource_id,
                                  id=id)
        if not data:
            data = resource_dict

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'edit',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
        return render('package/resource_edit.html', extra_vars=vars)

    def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        attr_errors = {}
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or \
                   clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                       request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']
            resource_id = data['id']
            del data['id']
            data['attributes'], attr_errors = _process_resource_attributes_list(data)

            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'auth_user_obj': c.userobj}

            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if ((value or isinstance(value, cgi.FieldStorage))
                    and key != 'resource_type'):
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    redirect(h.url_for(controller='package',
                                       action='edit', id=id))
                # see if we have added any resources
                try:
                    data_dict = get_action('package_show')(context, {'id': id})
                except NotAuthorized:
                    abort(403, _('Unauthorized to update dataset'))
                except NotFound:
                    abort(404, _('The dataset {id} could not be found.'
                                 ).format(id=id))
                if not len(data_dict['resources']):
                    # no data so keep on page
                    msg = _('You must add at least one data resource')
                    # On new templates do not use flash message
                    if g.legacy_templates:
                        h.flash_error(msg)
                        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors,
                                                 error_summary)
                # XXX race condition if another user edits/deletes
                data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))

            if any(attr_errors):
                errors = attr_errors
                error_summary = {}
                for key, val in errors.items():
                    error_summary.update({key: ' '.join(val)})
                return self.new_resource(id, data,
                                         errors, error_summary)
            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                errors.update(attr_errors)
                error_summary = e.error_summary
                return self.new_resource(id, data, errors, error_summary)
            except NotAuthorized:
                abort(403, _('Unauthorized to create a resource'))
            except NotFound:
                abort(404, _('The dataset {id} could not be found.'
                             ).format(id=id))
            if save_action == 'go-metadata':
                # XXX race condition if another user edits/deletes
                data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))

        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access(
                'resource_create', context, {"package_id": pkg_dict["id"]})
        except NotAuthorized:
            abort(403, _('Unauthorized to create a resource for this package'))

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        if any(attr_errors):
            errors.update(attr_errors)

        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
        vars['pkg_name'] = id
        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        template = 'package/new_resource_not_draft.html'
        if pkg_dict['state'].startswith('draft'):
            vars['stage'] = ['complete', 'active']
            template = 'package/new_resource.html'
        return render(template, extra_vars=vars)
