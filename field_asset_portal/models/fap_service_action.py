from odoo import api, fields, models


class FapServiceAction(models.Model):
    _name = 'fap.service.action'
    _description = 'Service Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Summary', required=True, tracking=True)
    ref = fields.Char(string='Reference', readonly=True, copy=False)
    asset_id = fields.Many2one('fap.asset', string='Asset', required=True, tracking=True)
    equipment_id = fields.Many2one(
        'fap.equipment', string='Equipment',
        domain="[('asset_id', '=', asset_id)]",
    )
    location_id = fields.Many2one(
        'fap.location', string='Location',
        related='asset_id.location_id', store=True, readonly=True,
    )
    action_type = fields.Selection(
        selection=[
            ('installation', 'Installation'),
            ('preventive', 'Preventive'),
            ('corrective', 'Corrective'),
            ('predictive', 'Predictive'),
            ('calibration', 'Calibration'),
            ('inspection', 'Inspection'),
            ('parts_replacement', 'Parts Replacement'),
        ],
        string='Type',
        required=True,
        default='corrective',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('draft', 'Approved'),
            ('confirmed', 'Confirmed'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('declined', 'Declined'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        required=True,
        default='draft',
        tracking=True,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Urgent'),
            ('2', 'Critical'),
        ],
        string='Priority',
        default='0',
    )
    requested_by_id = fields.Many2one('res.partner', string='Requested By')
    assigned_to_id = fields.Many2one('res.users', string='Assigned To', tracking=True)
    date_requested = fields.Datetime(string='Requested On', default=fields.Datetime.now)
    date_scheduled = fields.Datetime(string='Scheduled Date')
    date_completed = fields.Datetime(string='Completed On')
    description = fields.Html(string='Description')
    resolution = fields.Html(string='Resolution Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('fap.service.action') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_start(self):
        self.state = 'in_progress'

    def action_done(self):
        self.date_completed = fields.Datetime.now()
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset(self):
        self.state = 'draft'

    def action_set_pending(self):
        self.state = 'pending'

    def action_approve(self):
        self.state = 'draft'
        template = self.env.ref('field_asset_portal.mail_template_service_action_approved', raise_if_not_found=False)
        if template and self.requested_by_id and self.requested_by_id.email:
            template.send_mail(self.id, force_send=True)

    def action_decline(self):
        self.state = 'declined'
        template = self.env.ref('field_asset_portal.mail_template_service_action_declined', raise_if_not_found=False)
        if template and self.requested_by_id and self.requested_by_id.email:
            template.send_mail(self.id, force_send=True)
