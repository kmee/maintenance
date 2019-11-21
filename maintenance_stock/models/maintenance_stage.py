# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MaintenanceStage(models.Model):

    _inherit = 'maintenance.stage'

    can_return_use = fields.Boolean(
        string="Can return to use"
    )
