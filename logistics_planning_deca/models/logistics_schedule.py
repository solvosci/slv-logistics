# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from odoo import _, fields, models
from odoo.exceptions import UserError

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

    def _get_deca_url_path(self):
        self.ensure_one()
        return "logistics_schedule_deca/deca"

    def _get_deca_document_name(self):
        self.ensure_one()
        return "Waybill_%s.pdf" % (self.name or self.id)

    def _check_deca_can_generate_extra(self):
        self.ensure_one()
        if not self.deca_driver_id:
            raise UserError(_(
                "You must set a driver before generating the DeCA document."
            ))
        if not self.deca_signature:
            raise UserError(_(
                "You must provide a signature before generating the DeCA document."
            ))

    def _get_deca_report(self):
        self.ensure_one()
        return self.env.ref('logistics_planning_deca.action_report_logistics_schedule_deca')

    def action_portal_custom_action(self, requested_by=None):
        self.ensure_one()

        notified_users = (self.company_id or self.env.company).ls_portal_notification_user_ids
        if not notified_users:
            return

        recipient_emails = notified_users.mapped('email')
        recipient_emails = [email for email in recipient_emails if email]
        if not recipient_emails:
            return

        requester_name = requested_by.name if requested_by else _("Portal User")

        subject = _("DECA generated: %s") % self.display_name
        body_html = _(
            "<p><strong>%(user)s</strong> has generated the DECA document "
            "for logistics schedule <strong>%(schedule)s</strong>.</p>"
        ) % {
            'user': requester_name,
            'schedule': self.display_name,
        }

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body_html,
            'email_to': ','.join(recipient_emails),
            'auto_delete': True,
        }).send()
