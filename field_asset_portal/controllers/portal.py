from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class FieldAssetPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'asset_count' in counters:
            values['asset_count'] = request.env['fap.asset'].search_count([])
        return values

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
            'asset': asset,
            'equipment': equipment,
            'page_name': 'assets',
            'action_types': request.env['fap.service.action']._fields['action_type'].selection,
        })

    @http.route('/my/assets/<int:asset_id>/service/submit', type='http', auth='user', website=True, methods=['POST'])
    def portal_submit_service_action(self, asset_id, **kwargs):
        if not request.env['fap.asset'].search([('id', '=', asset_id)]).ids:
            return request.redirect('/my/assets')
        vals = {
            'asset_id': asset_id,
            'name': kwargs.get('name', ''),
            'action_type': kwargs.get('action_type', 'corrective'),
            'description': kwargs.get('description', ''),
            'requested_by_id': request.env.user.partner_id.id,
            'state': 'pending',
        }
        equipment_id = kwargs.get('equipment_id')
        if equipment_id:
            vals['equipment_id'] = int(equipment_id)
        request.env['fap.service.action'].sudo().create(vals)
        return request.redirect('/my/assets/%s' % asset_id)
