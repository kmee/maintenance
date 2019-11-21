# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MaintenanceEquipment(models.Model):

    _inherit = 'maintenance.equipment'

    def _get_default_maintenance_location(self):
        try:
            location = self.env.ref('maintenance_stock.stock_location_maintenance')
        except:
            location = False
        finally:
            return location


    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number'
    )
    maintenance_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Maintenance Location',
        default=_get_default_maintenance_location
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )

    @api.multi
    @api.onchange('lot_id')
    def _onchange_lot(self):
        for record in self:
            if record.lot_id:
                record.name = record.lot_id.product_id.name
                record.serial_no = record.lot_id.name
                record.product_id = record.product_id
