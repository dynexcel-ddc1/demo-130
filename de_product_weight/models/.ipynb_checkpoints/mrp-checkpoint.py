# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning


from odoo.addons import decimal_precision as dp

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    weight = fields.Float(related='product_id.weight',string='Weight/kg',readonly=True, store=True)
    total_weight = fields.Float('Total Weight', digits=dp.get_precision('Stock Weight'), help="Weight of the product in order line")
    
    @api.onchange('product_qty')
    def onchange_product_uom_qty(self):
        self.total_weight = self.product_id.weight * self.product_qty
		
	#def button_mark_done(self):
		#super(MrpProduction, self).button_mark_done()
