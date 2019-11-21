# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MaintenanceRequest(models.Model):

    _inherit = 'maintenance.request'

    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='maintenance_request_id',
        string='Related Pickings'
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial no',
        related='equipment_id.lot_id'
    )

    @api.multi
    def action_view_pickings(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view) for state, view in
                    action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_return_from_maintenance(self):
        for request in self:
            if not request.stage_id.can_return_use:
                raise ValidationError(_(
                    'This equipment can not be returned in '
                    'this stage of maintenance'
                ))

            if request.lot_id.quant_location_id != \
                    request.maintenance_team_id.location_id:
                raise ValidationError(_(
                    'This equipment is not in the maintenance team location, '
                    'it is in %s' % request.lot_id.quant_location_id.name
                ))

            if not request.lot_id.product_id.tracking == 'serial':
                raise ValidationError(_(
                    'This equipment tracking type is not by Serial No, '
                    'so this operation is not allowed'
                ))
            company = self.env.user.company_id.id
            warehouse_id = self.env['stock.warehouse'].search(
                [('company_id', '=', company)], limit=1)

            if request.picking_ids.filtered(
                lambda pick:
                pick.location_id == request.maintenance_team_id.location_id
                and pick.location_dest_id ==
                warehouse_id.rental_in_location_id and
                pick.state != 'cancel'
            ):
                raise ValidationError(_(
                    'This maintenance return already has a active picking'
                    ' and it can be accessed in \'View Pickings\' button'
                ))

            return_picking = self.env['stock.picking'].create({
                'partner_id': self.env.user.partner_id.id,
                'maintenance_request_id': request.id,
                'location_id': request.maintenance_team_id.location_id.id,
                'location_dest_id':
                    warehouse_id.rental_in_location_id.id,
                'product_id': request.lot_id.product_id.id,
                'picking_type_id': self.env.ref(
                    "maintenance_stock."
                    "picking_type_internal_maintenance"
                ).id
            })

            return_move = self.env['stock.move'].create({
                'name': request.name or '',
                'product_id': request.lot_id.product_id.id,
                'product_uom': request.lot_id.product_id.uom_id.id,
                'product_uom_qty': 1,
                'date': return_picking.date,
                'date_expected': return_picking.scheduled_date,
                'location_id': return_picking.location_id.id,
                'location_dest_id': return_picking.location_dest_id.id,
                'picking_id': return_picking.id,
                'partner_id': return_picking.partner_id.id,
                'state': 'draft',
                'company_id': return_picking.company_id.id,
                'price_unit': False,
                'picking_type_id': return_picking.picking_type_id.id,
                # 'group_id': self.out_move_id.group_id.id,
                # 'sale_line_id': self.start_order_line_id.id,
                'origin': request.name,
                # 'route_ids': [(6, 0, [picking.picking_type_id.warehouse_id.rental_return_route_id.id])],
                'warehouse_id': return_picking.picking_type_id.warehouse_id.id,
            })
            return_move._action_confirm()
            return_move._action_assign()
            for move_line in return_move.move_line_ids:
                if return_move.product_id == move_line.product_id:
                    move_line.lot_id = request.lot_id
