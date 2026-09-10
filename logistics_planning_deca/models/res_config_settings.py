# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ls_portal_notification_user_ids = fields.Many2one(
        related="company_id.ls_portal_notification_user_ids",
        readonly=False,
        required=True,
    )

class ResCompany(models.Model):
    _inherit = 'res.company'

    ls_portal_notification_user_ids = fields.Many2one(
        comodel_name="res.users",
        string="Users Notified of Portal Logistics DECa Generations",
    )
