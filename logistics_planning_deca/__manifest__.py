# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html
{
    'name': 'Logistics Planning DeCA',
    'summary': '''
        DeCA addon for logistics management
    ''',
    'author': 'Solvos',
    'license': 'LGPL-3',
    'version': '17.0.1.0.0',
    'category': 'stock',
    'website': 'https://github.com/solvosci/slv-logistics',
    'depends': ["logistics_planning_base", "l10n_es_stock_picking_deca"],
    'data': [
        'security/logistics_planning_deca_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/logistics_schedule_views.xml',
        'reports/stock_picking_template.xml',
        'templates/portal_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
}
