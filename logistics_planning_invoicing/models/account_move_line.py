# © 2024 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api
from odoo.osv import expression


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    logistics_schedule_id = fields.Many2one('logistics.schedule', copy=False)
    agg_logistics_schedule_ids = fields.Many2many(
        comodel_name="logistics.schedule",
        copy=False,
        string="Aggregated logistics schedules",
    )

    def _get_all_logistics_schedule_ids(self):
        return (
            self.logistics_schedule_id
            | self.agg_logistics_schedule_ids
        )

    @api.model_create_multi
    def create(self, vals_list):
        filtered_vals_list = []
        for vals in vals_list:
            # TODO we can receive values with this corner case situation:
            # * Has NO product
            # * Has logistics schedules linked
            # Such combination is disallowed and only could come from this addon
            # (not other invoicing process can generate it)
            # For such cases we should ignore values and skip line addition
            if not (
                (
                    vals.get('logistics_schedule_id')
                    or vals.get('agg_logistics_schedule_ids')
                )
                and not vals.get('product_id')
            ):
                filtered_vals_list.append(vals)

        lines = super().create(filtered_vals_list)
        for line in lines:
            all_ls_ids = line._get_all_logistics_schedule_ids().sudo()
            if all_ls_ids:
                all_ls_ids.write({
                    "account_move_line_id": line.id,
                })
                all_ls_ids._action_done()
        return lines

    def write(self, values):
        if "logistics_schedule_id" in values:
            logistics_schedule_id = (
                values.get("logistics_schedule_id")
                and self.env["logistics.schedule"].browse(values.get("logistics_schedule_id"))
                or False
            )
            if logistics_schedule_id:
                logistics_schedule_id.account_move_line_id = self
            else:
                self.logistics_schedule_id.account_move_line_id = False
        return super().write(values)

    @api.ondelete(at_uninstall=True)
    def _ls_secure_unlink(self):        
        ls_ids = self.sudo()._get_all_logistics_schedule_ids()
        if ls_ids:
            ls_ids.account_move_line_id.write({
                "logistics_schedule_id": False,
                "agg_logistics_schedule_ids": False,
            })
            ls_ids.write({
                "account_move_line_id": False,
                "state": "ready",
            })

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if self.env.context.get("logistics_planning_invoicing_existing", False) and name:
            domain = domain or []
            extra_domain = [
                ("name", operator, name),
            ]
            rec_ids = self._search(
                expression.AND([extra_domain, domain]), limit=limit, order=order,
            )
            records = self.browse(rec_ids).sorted(
                key=lambda x: (x.name or "")
            )
            return records.ids

        return super()._name_search(
            name=name, domain=domain, operator=operator, limit=limit, order=order
        )       

    @api.depends(
        "product_id.name",
        "move_id.name",
        "name",
        "price_unit",
        "company_currency_id.symbol",
        "quantity",
        "product_uom_id.name",
    )
    def _compute_display_name(self):
        if self.env.context.get('logistics_planning_invoicing_existing', False):
            for record in self:
                record.display_name = f"[{record.product_id.name}] {record.move_id.name}({record.name}) - {record.price_unit} {record.company_currency_id.symbol} ({record.quantity} {record.product_uom_id.name})"
        else:
            super()._compute_display_name()
