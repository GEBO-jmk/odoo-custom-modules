from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FapAsset(models.Model):
    _name = 'fap.asset'
    _description = 'Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string='Asset Name', required=True, tracking=True)
    ref = fields.Char(string='Internal Reference')
    location_id = fields.Many2one(
        'fap.location', string='Location', required=True, ondelete='cascade', tracking=True
    )
    contractor_id = fields.Many2one('res.partner', string='Contractor')
    service_company_id = fields.Many2one('res.partner', string='Service Company')
    warranty_start = fields.Date(string='Warranty Start')
    warranty_duration = fields.Integer(string='Warranty Duration (months)', default=12)
    warranty_end = fields.Date(
        string='Warranty End', compute='_compute_warranty_end', store=True
    )
    warranty_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('expiring_soon', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('not_set', 'Not Set'),
        ],
        string='Warranty Status',
        compute='_compute_warranty_status',
        store=True,
    )
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    equipment_ids = fields.One2many('fap.equipment', 'asset_id', string='Equipment')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Equipment')
    service_action_count = fields.Integer(compute='_compute_service_action_count', string='Service Actions')

    def _compute_equipment_count(self):
        for rec in self:
            rec.equipment_count = self.env['fap.equipment'].search_count([('asset_id', '=', rec.id)])

    def _compute_service_action_count(self):
        for rec in self:
            rec.service_action_count = self.env['fap.service.action'].search_count([('asset_id', '=', rec.id)])

    def action_open_equipment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment',
            'res_model': 'fap.equipment',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_open_service_actions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Actions',
            'res_model': 'fap.service.action',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    @api.depends('warranty_start', 'warranty_duration')
    def _compute_warranty_end(self):
        for rec in self:
            if rec.warranty_start and rec.warranty_duration:
                rec.warranty_end = rec.warranty_start + relativedelta(months=rec.warranty_duration)
            else:
                rec.warranty_end = False

    @api.depends('warranty_end')
    def _compute_warranty_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.warranty_end:
                rec.warranty_status = 'not_set'
            elif rec.warranty_end < today:
                rec.warranty_status = 'expired'
            elif rec.warranty_end < today + relativedelta(months=1):
                rec.warranty_status = 'expiring_soon'
            else:
                rec.warranty_status = 'active'
