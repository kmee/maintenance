# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MaintenanceTeam(models.Model):

    _inherit = 'maintenance.team'

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location'
    )
