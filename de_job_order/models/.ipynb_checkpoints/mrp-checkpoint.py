# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    categ_id = fields.Many2one("product.category", related='product_tmpl_id.categ_id', string="Category", readonly=True)
    
    compute_qty = fields.Selection([
        ('qty', 'By Quantity'),
        ('percentage', 'By Percentage'),
        ], index=True, default='qty', required=True)
    
    def _recursive_boms(self):
        """
        @return: returns a list of tuple (id) which are all the children of the passed bom_ids
        """
        children_boms = []
        for bom in self.filtered(lambda bom: bom.bom_line_ids.product_id.product_tmpl_id.bom_ids):
            children_boms += bom.bom_line_ids.product_id.product_tmpl_id.bom_ids._recursive_boms()
        return [(bom.id) for bom in self] + children_boms


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    percent_qty = fields.Float('Percentage Quantity')
    material_desc = fields.Char('Componenet Description')

    @api.onchange('percent_qty')
    def _onchange_percent_qty(self):
        for rs in self:
            if rs.bom_id.compute_qty == 'percentage':
                if rs.percent_qty > 0:
                    rs.product_qty = rs.bom_id.product_qty * (rs.percent_qty / 100)

class MRPProduction(models.Model):
    _inherit = 'mrp.production'
    
    job_order_id = fields.Many2one('job.order', string='Job Order', index=True, ondelete='cascade')
    #ref_sale_id = fields.Many2one('sale.order', string='Sale Order', required=False, ondelete='cascade', index=True, copy=False, readonly=True)
    categ_id = fields.Many2one("product.category", related='product_id.product_tmpl_id.categ_id', string="Category", readonly=True)
    
    #ref_sale_id = fields.Many2one("sale.order",compute="_assign_sale_order", store=False, readonly=True,)
    ref_sale_id = fields.Many2one("sale.order",related="job_order_id.sale_id", store=True, readonly=True,)
    
    def _assign_sale_order(self):
        #picking_id = self.id
        for line in self:
            query = """
        select distinct j.sale_id from job_order j
where j.id = %(job_order_id)s 
            """
            #self.env['stock.picking'].search([('name', '=', line.group_id.name)],limit=1).purchase_id.id
            params = {
                'job_order_id': line.job_order_id.id or 0,
                
            }
            self.env.cr.execute(query, params=params)
            #cr = self._cr
            for order in self._cr.dictfetchall():
                line.update ({
                    'ref_sale_id': order['sale_id'],
                })