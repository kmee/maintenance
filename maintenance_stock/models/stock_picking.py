# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    maintenance_request_id = fields.Many2one(
        comodel_name='maintenance.request'
    )
