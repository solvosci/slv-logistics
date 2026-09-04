# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class _DiscardTemporaryPicking(Exception):
    """ Internal exception used only to force the exit of the
    `with self.env.cr.savepoint():` block once we already have the PDF bytes
    in memory, so that the temporary picking created within that savepoint
    is undone and never persisted."""


class LogisticsSchedule(models.Model):
    _name = 'logistics.schedule'
    _inherit = ['logistics.schedule', 'deca.document.mixin']

    deca_driver_id = fields.Many2one(
        'res.partner',
        string="Chofer",
        help="Driver used to generate the carta de porte / DeCA document. "
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
        return self.env.ref('stock.action_report_delivery')

    def _render_deca_pdf(self, report):
        self.ensure_one()
        Picking = self.env['stock.picking'].sudo()

        pdf_content = None
        try:
            with self.env.cr.savepoint():
                picking = Picking.create(self._build_deca_picking_vals())

                report_data = self._get_deca_base_report_values()
                report_data['deca_sources'] = {picking.id: self}
                extra_data = self._get_deca_report_data()
                if extra_data:
                    report_data.update(extra_data)

                pdf_content, _report_type = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    report.id, picking.ids, data=report_data
                )

                _logger.info(
                    "Temporary picking %s created to render the DeCA "
                    "document for logistics.schedule %s; it will be "
                    "rolled back and never persisted.",
                    picking.id, self.id,
                )
                raise _DiscardTemporaryPicking()
        except _DiscardTemporaryPicking:
            pass

        return pdf_content

    def _build_deca_picking_vals(self):
        self.ensure_one()

        picking_type = self.picking_id.picking_type_id
        if not picking_type:
            raise UserError(_(
                "Cannot determine a picking type to generate the DeCA "
                "document for this schedule. Link it to a delivery order "
                "or configure a default picking type."
            ))

        return {
            'partner_id': self.destination_partner_id.id or self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'company_id': self.company_id.id,
            'origin': self.origin or self.name,
            'scheduled_date': self.commitment_date or fields.Datetime.now(),
            'note': self.note,
            'move_ids': [(0, 0, self._build_deca_move_vals(picking_type))],
        }

    def _build_deca_move_vals(self, picking_type):
        self.ensure_one()
        return {
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'company_id': self.company_id.id,
        }
