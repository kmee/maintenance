# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Maintenance Stock',
    'summary': """
        Link maintenance with stock moves""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'maintenance',
        'stock',
        'idealcare_sale_rental'
    ],
    'data': [
        # 'security/maintenance_stage.xml',
        'views/maintenance_stage.xml',
        'data/stock_location_data.xml',
        'data/stock_picking_type_data.xml',
        # 'security/stock_picking.xml',
        # 'views/stock_picking.xml',
        # 'security/maintenance_request.xml',
        'views/stock_production_lot.xml',
        'views/maintenance_request.xml',
        # 'security/stock_production_lot.xml',
        # 'security/maintenance_team.xml',
        'views/maintenance_team.xml',
        # 'security/maintenance_equipment.xml',
        'views/maintenance_equipment.xml',
    ],
    'demo': [
        # 'demo/stock_picking.xml',
        # 'demo/maintenance_request.xml',
        # 'demo/stock_production_lot.xml',
        # 'demo/maintenance_team.xml',
        # 'demo/maintenance_equipment.xml',
    ],
    'installable': True
}

