# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.tools import float_is_zero


class WizardCreateMaintenance(models.TransientModel):

    _name = 'create.maintenance.wizard'

    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance.team',
    )
    description = fields.Text(
        string='Equipament problem',
    )

    @api.multi
    def action_maintenance(self):
        for lot in self.env['stock.production.lot'].browse(
                self.env.context.get('active_ids')):

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
                    'owner_user_id': maint_equipment.owner_user_id and
                                     maint_equipment.owner_user_id.id or
                                     self.env.user.id,
                    'user_id': maint_equipment.technician_user_id.id,
                    'maintenance_team_id': self.maintenance_team_id.id,
                    'duration': maint_equipment.maintenance_duration,
                    'description': self.description,
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
                    'name': lot.name or '',
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

            precision_digits = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')

            no_quantities_done = all(
                float_is_zero(
                    move_line.qty_done, precision_digits=precision_digits)
                for move_line in picking.move_line_ids.filtered(
                        lambda m: m.state not in ('done', 'cancel'))
            )
            if no_quantities_done:
                self.env['stock.immediate.transfer'].create(
                    {'pick_ids': [(4, picking.id)]}
                ).process()

            elif self._get_overprocessed_stock_moves():
                self.env['stock.overprocessed.transfer'].create(
                    {'picking_id': picking.id}
                ).process()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'maintenance.request',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': maint_request.id,
            }

