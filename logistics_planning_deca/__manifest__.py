# © 2023 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html
{
    'name': 'Logistics Planning Deca',
    'summary': '''
        Deca addon for logistics management
    ''',
    'author': 'Solvos',
    'license': 'LGPL-3',
    'version': '17.0.1.0.0',
    'category': 'stock',
    'website': 'https://github.com/solvosci/slv-logistics',
    'depends': ["logistics_planning_base", "l10n_es_stock_picking_deca"],
    'data': [
        'views/logistics_schedule_views.xml',
        #'reports/report_delivery_slip.xml',
    ],
    'installable': True,
}
