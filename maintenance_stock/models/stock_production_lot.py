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
        for lot in self:
            if lot.quant_location_id.usage != 'internal':
                raise ValidationError(_("This equipment is not in stock "
                                     "to go to maintenance")
                                  )

            maint_equipment = self.env['maintenance.equipment'].search(
                [('lot_id', '=', lot.id)]
            )
            if not maint_equipment:
                maint_equipment = self.env['maintenance.equipment'].create(
                    {
                        'lot_id': lot.id,
                        'name': lot.product_id.name + ' (' + lot.name + ')',
                        'product_id': lot.product_id.id,
                    }
                )
            maint_request = self.env['maintenance.request'].create(
                {
                    'name': _('Maintenance - %s') % maint_equipment.name,
                    'request_date': fields.Date.today(),
                    'schedule_date': fields.Date.today(),
                    'category_id': maint_equipment.category_id.id,
                    'equipment_id': maint_equipment.id,
                    'maintenance_type': 'corrective',
                    'owner_user_id': maint_equipment.owner_user_id.id,
                    'user_id': maint_equipment.technician_user_id.id,
                    'maintenance_team_id': self.env.ref(
                        "maintenance.equipment_team_maintenance").id,
                    'duration': maint_equipment.maintenance_duration,
                }
            )
            lot.maintenance_ids += maint_request

            if lot.product_id.tracking == 'serial':
                Picking = self.env['stock.picking']
                picking = Picking.create(
                    {
                        'partner_id': self.env.user.partner_id.id,
                        'maintenance_request_id': maint_request.id,
                        'location_id': lot.quant_location_id.id,
                        'location_dest_id':
                            maint_request.maintenance_team_id.location_id.id,
                        # 'product_id': maint_equipment.product_id.id,
                        'picking_type_id': self.env.ref(
                            "maintenance_stock."
                            "picking_type_internal_maintenance"
                        ).id
                    }
                )

                move = self.env['stock.move'].create({
                    'name': self.name or '',
                    'product_id': lot.product_id.id,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uom_qty': 1,
                    'date': picking.date,
                    'date_expected': picking.scheduled_date,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'picking_id': picking.id,
                    'partner_id': picking.partner_id.id,
                    'state': 'draft',
                    'company_id': picking.company_id.id,
                    'price_unit': False,
                    'picking_type_id': picking.picking_type_id.id,
                    # 'group_id': self.out_move_id.group_id.id,
                    # 'sale_line_id': self.start_order_line_id.id,
                    'origin': maint_request.name,
                    # 'route_ids': [(6, 0, [picking.picking_type_id.warehouse_id.rental_return_route_id.id])],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                })
                move._action_confirm()
                move._action_assign()
                for move_line in move.move_line_ids:
                    if move.product_id == move_line.product_id:
                        move_line.lot_id = lot
