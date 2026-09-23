import base64

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo import http
from odoo.http import request


class LogisticsScheduleCustomerPortal(CustomerPortal):

    def _get_schedule_sudo(self, schedule_id, access_token=None):
        schedule_sudo = self._document_check_access(
            'logistics.schedule', schedule_id, access_token=access_token
        )
        if schedule_sudo.partner_id != request.env.user.partner_id or \
            schedule_sudo.state != 'ready' or schedule_sudo.schedule_finished:
            raise AccessError("You do not have access to this record.")
        return schedule_sudo

    def _get_schedule_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
            ('state', '=', 'ready'),
            ('schedule_finished', '=', False),
        ]

    def _get_schedule_searchbar_sortings(self):
        return {
            'date': {'label': 'Load Date', 'order': 'scheduled_load_date desc'},
            'name': {'label': 'Reference', 'order': 'name'},
            'state': {'label': 'Status', 'order': 'state'},
        }

    def _get_available_drivers(self, carrier_id=None):
        domain = [
            ('is_company', '=', False),
            '|', ('company_id', '=', False), ('company_id', '=', request.env.company.id),
        ]
        if carrier_id:
            domain.append(('parent_id', '=', carrier_id))
        return request.env['res.partner'].sudo().search(domain, order='name')

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'schedule_count' in counters:
            partner = request.env.user.partner_id
            Schedule = request.env['logistics.schedule']
            schedule_count = Schedule.search_count(
                self._get_schedule_domain(partner), limit=1
            ) if Schedule.check_access_rights('read', raise_exception=False) else 0
            values['schedule_count'] = schedule_count
        return values

    @http.route(['/my/schedules', '/my/schedules/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_schedules(self, page=1, sortby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Schedule = request.env['logistics.schedule'].sudo()

        domain = self._get_schedule_domain(partner)

        searchbar_sortings = self._get_schedule_searchbar_sortings()
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if search and search_in:
            domain += [
                '|',
                ('name', 'ilike', search),
                ('origin', 'ilike', search),
            ]

        schedule_count = Schedule.search_count(domain)

        pager = portal_pager(
            url="/my/schedules",
            url_args={'sortby': sortby, 'search': search, 'search_in': search_in},
            total=schedule_count,
            page=page,
            step=self._items_per_page,
        )

        schedules = Schedule.search(
            domain, order=order,
            limit=self._items_per_page,
            offset=pager['offset'],
        )

        values.update({
            'schedules': schedules,
            'page_name': 'schedule',
            'pager': pager,
            'default_url': '/my/schedules',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render(
            "logistics_planning_deca.portal_my_schedules", values
        )

    @http.route(['/my/schedules/<int:schedule_id>'], type='http', auth='user', website=True)
    def portal_schedule_detail(self, schedule_id, access_token=None, message=None, error=None, **kw):
        try:
            schedule_sudo = self._get_schedule_sudo(schedule_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'schedule': schedule_sudo,
            'page_name': 'schedule',
            'message': message,
            'error': error,
            'available_drivers': self._get_available_drivers(schedule_sudo.carrier_id.id),
        }
        return request.render(
            "logistics_planning_deca.portal_schedule_detail", values
        )

    @http.route(['/my/schedules/<int:schedule_id>/update'], type='http', auth='user', website=True, methods=['POST'])
    def portal_schedule_update(self, schedule_id, **post):
        try:
            schedule_sudo = self._get_schedule_sudo(schedule_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        driver_id = post.get('deca_driver_id')
        vals = {
            'deca_driver_id': int(driver_id) if driver_id else False,
            'license_plate_1': post.get('license_plate_1') or False,
            'license_plate_2': post.get('license_plate_2') or False,
        }

        signature = post.get('deca_signature')
        if signature and ',' in signature:
            vals['deca_signature'] = signature.split(',', 1)[1]

        schedule_sudo.write(vals)
        return request.redirect(f'/my/schedules/{schedule_id}?message=updated')

    @http.route(['/my/schedules/<int:schedule_id>/sign/clear'], type='http', auth='user', website=True, methods=['POST'])
    def portal_schedule_sign_clear(self, schedule_id, **post):
        try:
            schedule_sudo = self._get_schedule_sudo(schedule_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        schedule_sudo.write({'deca_signature': False})
        return request.redirect(f'/my/schedules/{schedule_id}')

    @http.route(['/my/schedules/<int:schedule_id>/generate_deca'], type='http', auth='user', website=True, methods=['POST'])
    def portal_schedule_generate_deca(self, schedule_id, **post):
        try:
            schedule_sudo = self._get_schedule_sudo(schedule_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        try:
            schedule_sudo.action_generate_deca()
            schedule_sudo.send_mail_notification_deca_portal(requested_by=request.env.user.partner_id)
        except Exception as e:
            return request.redirect(f'/my/schedules/{schedule_id}?error={str(e)}')
        return request.redirect(f'/my/schedules/{schedule_id}?message=action_done')

    @http.route(['/my/schedules/<int:schedule_id>/document'], type='http', auth='user', website=True)
    def portal_schedule_document(self, schedule_id, **kw):
        try:
            schedule_sudo = self._get_schedule_sudo(schedule_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        attachment = schedule_sudo.deca_attachment_id
        if not attachment or not attachment.datas:
            return request.not_found()

        return request.make_response(
            base64.b64decode(attachment.datas),
            headers=[
                ('Content-Type', attachment.mimetype or 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{attachment.name or "document.pdf"}"'),
            ],
        )
