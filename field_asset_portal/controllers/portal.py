from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class FieldAssetPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'asset_count' in counters:
            partner = request.env.user.partner_id
            values['asset_count'] = request.env['fap.asset'].search_count([
                '|', '|', '|',
                ('location_id.owner_id', 'child_of', partner.commercial_partner_id.id),
                ('contractor_id', 'child_of', partner.commercial_partner_id.id),
                ('service_company_id', 'child_of', partner.commercial_partner_id.id),
                ('equipment_ids.service_company_id', 'child_of', partner.commercial_partner_id.id),
            ])
        return values

    @http.route('/my/locations', type='http', auth='user', website=True)
    def portal_my_locations(self, **kwargs):
        location_ids = request.env['fap.location'].search([]).ids
        locations = request.env['fap.location'].sudo().browse(location_ids)
        return request.render('field_asset_portal.portal_my_locations', {
            'locations': locations,
            'page_name': 'locations',
        })

    @http.route('/my/assets', type='http', auth='user', website=True)
    def portal_my_assets(self, **kwargs):
        asset_ids = request.env['fap.asset'].search([]).ids
        assets = request.env['fap.asset'].sudo().browse(asset_ids)
        return request.render('field_asset_portal.portal_my_assets', {
            'assets': assets,
            'page_name': 'assets',
        })

    @http.route('/my/assets/<int:asset_id>', type='http', auth='user', website=True)
    def portal_asset_detail(self, asset_id, **kwargs):
        asset_ids = request.env['fap.asset'].search([('id', '=', asset_id)]).ids
        if not asset_ids:
            return request.redirect('/my/assets')
        asset = request.env['fap.asset'].sudo().browse(asset_ids[0])
        equipment_ids = request.env['fap.equipment'].search([('asset_id', '=', asset_id)]).ids
        equipment = request.env['fap.equipment'].sudo().browse(equipment_ids)
        service_action_ids = request.env['fap.service.action'].search(
            [('asset_id', '=', asset_id)], order='date_requested desc'
        ).ids
        service_actions = request.env['fap.service.action'].sudo().browse(service_action_ids)
        return request.render('field_asset_portal.portal_asset_detail', {
            'asset': asset,
            'equipment': equipment,
            'service_actions': service_actions,
            'page_name': 'assets',
        })

    @http.route('/my/assets/<int:asset_id>/service/new', type='http', auth='user', website=True)
    def portal_new_service_action(self, asset_id, **kwargs):
        asset_ids = request.env['fap.asset'].search([('id', '=', asset_id)]).ids
        if not asset_ids:
            return request.redirect('/my/assets')
        asset = request.env['fap.asset'].sudo().browse(asset_ids[0])
        equipment_ids = request.env['fap.equipment'].search([('asset_id', '=', asset_id)]).ids
        equipment = request.env['fap.equipment'].sudo().browse(equipment_ids)
        return request.render('field_asset_portal.portal_new_service_action', {
            'location': asset.location_id,
            'asset': asset,
            'assets': request.env['fap.asset'].sudo().browse([asset_id]),
            'equipment': equipment,
            'page_name': 'assets',
            'action_types': request.env['fap.service.action']._fields['action_type'].selection,
        })

    @http.route('/my/locations/<int:location_id>/service/new', type='http', auth='user', website=True)
    def portal_new_service_from_location(self, location_id, **kwargs):
        location_ids = request.env['fap.location'].search([('id', '=', location_id)]).ids
        if not location_ids:
            return request.redirect('/my/assets')
        location = request.env['fap.location'].sudo().browse(location_ids[0])
        asset_ids = request.env['fap.asset'].search([('location_id', '=', location_id)]).ids
        assets = request.env['fap.asset'].sudo().browse(asset_ids)
        return request.render('field_asset_portal.portal_new_service_action', {
            'location': location,
            'assets': assets,
            'equipment': request.env['fap.equipment'].sudo().browse([]),
            'page_name': 'assets',
            'action_types': request.env['fap.service.action']._fields['action_type'].selection,
        })

    @http.route('/my/equipment/<int:equipment_id>/service/new', type='http', auth='user', website=True)
    def portal_new_service_from_equipment(self, equipment_id, **kwargs):
        equipment_ids = request.env['fap.equipment'].search([('id', '=', equipment_id)]).ids
        if not equipment_ids:
            return request.redirect('/my/assets')
        equipment = request.env['fap.equipment'].sudo().browse(equipment_ids[0])
        asset = equipment.asset_id
        all_equipment_ids = request.env['fap.equipment'].search([('asset_id', '=', asset.id)]).ids
        all_equipment = request.env['fap.equipment'].sudo().browse(all_equipment_ids)
        return request.render('field_asset_portal.portal_new_service_action', {
            'location': asset.location_id,
            'asset': asset,
            'assets': request.env['fap.asset'].sudo().browse([asset.id]),
            'equipment': all_equipment,
            'preselected_equipment_id': equipment_id,
            'page_name': 'assets',
            'action_types': request.env['fap.service.action']._fields['action_type'].selection,
        })

    @http.route('/my/service/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_submit_service_action(self, **kwargs):
        asset_id = kwargs.get('asset_id')
        vals = {
            'name': kwargs.get('name', ''),
            'action_type': kwargs.get('action_type', 'corrective'),
            'description': kwargs.get('description', ''),
            'requested_by_id': request.env.user.partner_id.id,
            'state': 'pending',
        }
        if asset_id:
            asset_ids = request.env['fap.asset'].search([('id', '=', int(asset_id))]).ids
            if asset_ids:
                vals['asset_id'] = int(asset_id)
        equipment_id = kwargs.get('equipment_id')
        if equipment_id:
            vals['equipment_id'] = int(equipment_id)
        request.env['fap.service.action'].sudo().create(vals)
        redirect = '/my/assets/%s' % asset_id if asset_id else '/my/assets'
        return request.redirect(redirect)
