from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FapEquipment(models.Model):
    _name = 'fap.equipment'
    _description = 'Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    asset_id = fields.Many2one(
        'fap.asset', string='Asset', required=True, ondelete='cascade', tracking=True
    )
    location_id = fields.Many2one(
        'fap.location', string='Location',
        related='asset_id.location_id', store=True, readonly=True,
    )
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')
    manufacturer_part_code = fields.Char(string='Manufacturer Part Code')
    manufacturer_serial = fields.Char(string='Manufacturer Serial Number')
    your_part_code = fields.Char(string='Our Part Code')
    your_serial = fields.Char(string='Our Serial Number')

    manufacturer_warranty_start = fields.Date(string='Manufacturer Warranty Start')
    manufacturer_warranty_duration = fields.Integer(
        string='Manufacturer Warranty (months)', default=12
    )
    manufacturer_warranty_end = fields.Date(
        string='Manufacturer Warranty End',
        compute='_compute_manufacturer_warranty_end',
        store=True,
    )
    manufacturer_warranty_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('expiring_soon', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('not_set', 'Not Set'),
        ],
        string='Manufacturer Warranty Status',
        compute='_compute_manufacturer_warranty_status',
        store=True,
    )

    our_warranty_start = fields.Date(string='Our Warranty Start')
    our_warranty_duration = fields.Integer(string='Our Warranty (months)', default=12)
    our_warranty_end = fields.Date(
        string='Our Warranty End',
        compute='_compute_our_warranty_end',
        store=True,
    )
    our_warranty_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('expiring_soon', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('not_set', 'Not Set'),
        ],
        string='Our Warranty Status',
        compute='_compute_our_warranty_status',
        store=True,
    )

    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    service_action_count = fields.Integer(compute='_compute_service_action_count', string='Service Actions')

    def _compute_service_action_count(self):
        for rec in self:
            rec.service_action_count = self.env['fap.service.action'].search_count([('equipment_id', '=', rec.id)])

    @api.depends('manufacturer_warranty_start', 'manufacturer_warranty_duration')
    def _compute_manufacturer_warranty_end(self):
        for rec in self:
            if rec.manufacturer_warranty_start and rec.manufacturer_warranty_duration:
                rec.manufacturer_warranty_end = (
                    rec.manufacturer_warranty_start
                    + relativedelta(months=rec.manufacturer_warranty_duration)
                )
            else:
                rec.manufacturer_warranty_end = False

    @api.depends('manufacturer_warranty_end')
    def _compute_manufacturer_warranty_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.manufacturer_warranty_end:
                rec.manufacturer_warranty_status = 'not_set'
            elif rec.manufacturer_warranty_end < today:
                rec.manufacturer_warranty_status = 'expired'
            elif rec.manufacturer_warranty_end < today + relativedelta(months=1):
                rec.manufacturer_warranty_status = 'expiring_soon'
            else:
                rec.manufacturer_warranty_status = 'active'

    @api.depends('our_warranty_start', 'our_warranty_duration')
    def _compute_our_warranty_end(self):
        for rec in self:
            if rec.our_warranty_start and rec.our_warranty_duration:
                rec.our_warranty_end = (
                    rec.our_warranty_start + relativedelta(months=rec.our_warranty_duration)
                )
            else:
                rec.our_warranty_end = False

    @api.depends('our_warranty_end')
    def _compute_our_warranty_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.our_warranty_end:
                rec.our_warranty_status = 'not_set'
            elif rec.our_warranty_end < today:
                rec.our_warranty_status = 'expired'
            elif rec.our_warranty_end < today + relativedelta(months=1):
                rec.our_warranty_status = 'expiring_soon'
            else:
                rec.our_warranty_status = 'active'
