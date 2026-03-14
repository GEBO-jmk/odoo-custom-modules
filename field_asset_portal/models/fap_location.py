from odoo import api, fields, models


class FapLocation(models.Model):
    _name = 'fap.location'
    _description = 'Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Location Name', required=True, tracking=True)
    ref = fields.Char(string='Reference')
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one('res.country.state')
    owner_id = fields.Many2one('res.partner', string='Site Owner', required=True, tracking=True)
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    asset_ids = fields.One2many('fap.asset', 'location_id', string='Assets')
    asset_count = fields.Integer(compute='_compute_asset_count', string='Assets')

    def _compute_asset_count(self):
        for rec in self:
            rec.asset_count = self.env['fap.asset'].search_count([('location_id', '=', rec.id)])
