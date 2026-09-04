# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from odoo import http
from odoo.http import request
from odoo.addons.l10n_es_stock_picking_deca.controllers.main import StockPickingDecaController
from werkzeug.exceptions import Forbidden


class LogisticsScheduleDecaController(StockPickingDecaController):

    @http.route(
        '/deca/sched/<string:hash_code>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def deca_document_planning(self, hash_code, **kwargs):
        return self.get_deca_document(
            hash_code,
            model="logistics.schedule",
            **kwargs
        )
