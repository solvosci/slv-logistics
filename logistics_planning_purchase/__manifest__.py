# © 2024 Solvos Consultoría Informática (<http://www.solvos.es>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html
{
    'name': 'Logistics Planning Purchase',
    'summary': '''
        Links Logistics Planning with Purchases
    ''',
    'author': 'Solvos',
    'license': 'LGPL-3',
    'version': '17.0.1.0.0',
    'category': 'stock',
    'website': 'https://github.com/solvosci/slv-logistics',
    'depends': [
        'purchase_stock',
        'logistics_planning_invoicing',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/logistics_schedule_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_type_views.xml',
        'views/res_config_settings_views.xml',
        'wizards/logistics_schedule_purchase_add_wizard_views.xml',
    ],
}
