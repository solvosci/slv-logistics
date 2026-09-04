# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ls_portal_notification_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="res_user_res_company_deca_notified",
        string="Users Notified of Portal Logistics DeCA Generations",
    )
    ls_deca_sequence = fields.Char(
        string="Sequence given to DeCA Documents generated in logistics",
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ls_portal_notification_user_ids = fields.Many2many(
        related="company_id.ls_portal_notification_user_ids",
        readonly=False,
        required=True,
    )
    ls_deca_sequence = fields.Char(
        related="company_id.ls_deca_sequence",
        readonly=False,
        required=True,
    )

