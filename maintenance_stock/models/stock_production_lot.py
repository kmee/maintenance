# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    maintenance_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='lot_id'
    )
    maintenances_count = fields.Integer(
        string='Rentals',
        compute='_compute_maintenances'
    )
    available_maintenance = fields.Boolean(
        compute='_compute_available_for_maintenance'
    )

    @api.multi
    def _compute_available_for_maintenance(self):
        wh_id = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)],
            limit=1
        )
        available_location_id = wh_id.rental_in_location_id
        for record in self:
            if record.quant_location_id == available_location_id:
                record.available_maintenance = True
            else:
                record.available_maintenance = False

    @api.multi
    def action_view_maintenances(self):
        action = self.env.ref('maintenance.hr_equipment_request_action').read()[0]
        # action['context'] = {
        #     'search_default_order_stage_id': 1,
        # }

        maintenances = self.maintenance_ids

        if len(maintenances) > 1:
            action['domain'] = [('id', 'in', maintenances.ids)]
        elif maintenances:
            action['views'] = [(
                self.env.ref('maintenance.hr_equipment_request_view_form').id,
                'form')]
            action['res_id'] = maintenances.id
        return action

    @api.depends('maintenance_ids')
    def _compute_maintenances(self):
        for lot in self:
            lot.maintenances_count = len(lot.maintenance_ids)

    @api.multi
    def action_maintenance(self):
        self.ensure_one()
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)

        if self.quant_location_id != wh.rental_in_location_id:
            raise ValidationError(_("This equipment is not in available "
                                    "stock to go to maintenance")
                                  )
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'create.maintenance.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }
