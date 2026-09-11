# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from odoo import http
from odoo.http import request
from werkzeug.exceptions import Forbidden


class LogisticsScheduleDecaController(http.Controller):

    @http.route(
        '/logistics_schedule_deca/deca/<int:logistics_id>',
        type='http',
        auth='public',
        website=False,
        csrf=False,
    )
    def deca_document(self, logistics_id, **kwargs):
        logistics = request.env['logistics.schedule'].sudo().browse(logistics_id)

        if not logistics.exists() or not logistics.deca_is_generated or not logistics.deca_attachment_id:
            raise Forbidden()

        attachment = logistics.deca_attachment_id
        pdf_content = base64.b64decode(attachment.datas or b'')

        if not pdf_content:
            raise Forbidden()

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'inline; filename="%s"' % (attachment.name or 'DeCA.pdf')),
            ('Content-Length', len(pdf_content)),
        ]
        return request.make_response(pdf_content, headers=headers)
