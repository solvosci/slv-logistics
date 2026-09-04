# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

import logging
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class LogisticsSchedule(models.Model):
    _name = 'logistics.schedule'
    _inherit = ['logistics.schedule', 'deca.document.mixin']

    deca_driver_id = fields.Many2one(
        'res.partner',
        string="Driver",
    )
    deca_signature = fields.Binary(
        string="DeCA Signature",
        copy=False,
        help="Signature required to generate the DeCA document.",
    )
    deca_sequence = fields.Char(
        compute="_compute_deca_sequence",
    )

    def _get_deca_url_path(self):
        self.ensure_one()
        return "deca/sched"

    def _get_deca_document_name(self):
        self.ensure_one()
        return "Waybill_%s.pdf" % (self.name or self.id)

    def _check_deca_can_generate_extra(self):
        for record in self:
            if not record.deca_driver_id:
                raise UserError(_(
                    "You must set a driver before generating the DeCA document."
                ))
            if not record.deca_signature:
                raise UserError(_(
                    "You must provide a signature before generating the DeCA document."
                ))
            if not record.deca_sequence:
                raise UserError(_(
                    "The DeCA sequence is not set. Please check the company settings."
                ))

    def _get_deca_report(self):
        self.ensure_one()
        return self.env.ref('logistics_planning_deca.action_report_logistics_schedule_deca_waybill')

    def _compute_deca_sequence(self):
        edit_sched = self.filtered(lambda s: s.company_id.ls_deca_sequence)
        for schedule in edit_sched:
            schedule.deca_sequence = "%s/%d" % (
                schedule.company_id.ls_deca_sequence.rstrip("/"),
                schedule.id
            )
        (self - edit_sched).update({"deca_sequence": False})

    def send_mail_notification_deca_portal(self, requested_by=None):
        self.ensure_one()

        notified_users = (self.company_id or self.env.company).ls_portal_notification_user_ids
        if not notified_users:
            return

        requester_name = requested_by.name if requested_by else _("Portal User")

        template = self.env.ref(
            'logistics_planning_deca.mail_template_deca_portal_notification'
        )
        return template.with_context(requester_name=requester_name).send_mail(
            self.id,
            email_values={
                'recipient_ids': [Command.set(notified_users.partner_id.ids)],
            },
            force_send=True,
        )
