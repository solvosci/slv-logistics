# © 2023 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, models, fields
from odoo.osv import expression


class StockMove(models.Model):
    _inherit = 'stock.move'

    logistics_schedule_id = fields.Many2one('logistics.schedule', copy=False)
    logistics_schedule_disabled = fields.Boolean(copy=False)

    warehouse_partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_warehouse_partner_id",
        store=True,        
        string="Warehouse Partner",
        help="""
        Technical field enables us accessing partner for the origin location
        warehouse for this move.
        We'll only calculate it for internal transfers.
        """,
    )

    @api.depends("location_id", "picking_code")
    def _compute_warehouse_partner_id(self):
        # TODO move to read_group() for faster initialization during installation?
        internal_moves = self.filtered(
            lambda x: (
                x.picking_code == "internal"
                and x.location_id.usage == "internal"
            )
        )
        for move in internal_moves:
            move.warehouse_partner_id = move.location_id.warehouse_id.partner_id
        (self - internal_moves).update({"warehouse_partner_id": False})

    def _prepare_name_get(self):
        return (
            "%s (%.3f %s)"
            %
            (self.picking_id.name, self.product_uom_qty, self.product_uom.name)
        )

    @api.depends("picking_id.name", "product_uom_qty", "product_uom.name")
    def _compute_display_name(self):
        if self.env.context.get("logistics_schedule_view", False):
            for record in self:
                record.display_name = record._prepare_name_get()
        else:
            super(StockMove, self)._compute_display_name()

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        """
        If we comes from logistics schedule, we add picking and product search,
        and sorted by picking
        """
        if self.env.context.get("logistics_schedule_view", False) and name:
            domain = domain or []
            extra_domain = [
                "|",
                ("picking_id.name", operator, name),
                "|",
                ("product_id.default_code", operator, name),
                ("product_id.name", operator, name),
            ]
            rec_ids = self._search(
                expression.AND([extra_domain, domain]), limit=limit, order=order,
            )
            records = self.browse(rec_ids).sorted(
                key=lambda x: (x.picking_id.name or "")
            )
            return records.ids

        return super()._name_search(
            name=name, domain=domain, operator=operator, limit=limit, order=order
        )
