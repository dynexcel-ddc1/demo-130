# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning


from odoo.addons import decimal_precision as dp


class JobOrder(models.Model):
    _name = 'job.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Job Order'
    _order = 'date_order desc, id desc'
    
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    
    struct_id = fields.Many2one('job.order.structure', string='Structure',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Defines the rules that have to be applied to this Job Order, accordingly ')
    
    sale_id = fields.Many2one('sale.order', 'Order Reference',required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('processed', 'Processed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    
    date_order = fields.Datetime(string='Job Order Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    
    note = fields.Text(string="Note")
    
    job_order_lines = fields.One2many('job.order.line', 'job_order_id', string='Job Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    
    job_order_sale_lines = fields.One2many('job.order.sale.line', 'job_order_id', string='Order Sale Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    
    job_order_mrp_ids = fields.One2many('job.order.mrp', 'job_order_id', string='Job Order MRP Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    
    #details_by_component = fields.One2many('hr.payslip.line',compute='_compute_details_by_salary_rule_category', string='Details by Salary Rule Category')
    
    details_by_category = fields.One2many('job.order.line', compute='_compute_details_by_category', string='Details by Category')
    
    bom_ids = fields.One2many('mrp.bom', 'product_tmpl_id', string='Bill of Materials')
    bom_count = fields.Integer(string='BOMs', compute='_compute_bom_ids')
    
    def _compute_details_by_category(self):
        for job in self:
            job.details_by_category = job.mapped('job_order_lines').filtered(lambda line: line.category_id)
            
    @api.depends('bom_ids')
    def _compute_bom_ids(self):
        b = 0
        for order in self:
            for line in order.job_order_lines:
                b = len(line.product_tmpl_id.bom_ids)
            order.bom_count = b
    
    def action_view_bom(self):
        action = self.env.ref('mrp.mrp_bom_tree_view').read()[0]

        boms = self.mapped('boms_ids')
        if len(boms) > 1:
            action['domain'] = [('id', 'in', boms.ids)]
        elif boms:
            action['views'] = [(self.env.ref('mrp.mrp_bom_form_view').id, 'form')]
            action['res_id'] = boms.id
        return action
    
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('job.order') or ' '
        res_id = super(JobOrder, self).create(vals)
        return res_id
    
    def generate_orders(self):
        bom_ids = []
        primary_bom_ids = []
        all_boms = []
        product_id = 0
        var1 = ''
        rule_qty = 0
        #self.state = 'processed'
        #finish_production_id = self.env['mrp.production']
        #semi_production_id = self.env['mrp.production']
        for line in self.job_order_sale_lines:
            #bom_ids = self.env['mrp.bom'].browse(line.bom_id).id
            fvals = {
                'product_id': line.product_id.id,
                'product_uom_id':line.product_id.uom_id.id,
                'product_qty':line.product_uom_qty,
                'bom_id':line.bom_id.id,
                'origin':self.sale_id.name,
                #'orderpoint_id':self.sale_id.id,
                'job_order_id': self.id,
                'ref_sale_id':self.sale_id.id,
            }
            finish_production_id = self.env['mrp.production'].create(fvals)
            self.env.cr.commit()

            if not (line.bom_id in bom_ids):
                bom_ids.append(line.bom_id)
            
        for boms in bom_ids:
            #var1 = var1 + ',' + p
            #var1 = var1 + '--' + str(boms.id)
            all_boms += boms._recursive_boms()
            #var1 = var1 + ',' + str(all_boms)
            primary_bom_ids.append(boms.id)
            #var1 = str(primary_bom_ids)
        #sub_boms = self.env['mrp.bom'].search([('id', 'in', all_boms ),('id', 'not in', primary_bom_ids )])
        #for bom in sub_boms:
            
            #product_id1 = self.env['product.product'].search([('product_tmpl_id', '=', bom.product_tmpl_id.id )],limit=1)
            #vendor_id = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', bom.product_tmpl_id.id )]).name
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            
            #self.env.cr.execute('select l.quantity from job_order o join job_order_sale_line s on s.job_order_id = o.id join job_order_line l on l.job_sale_line_id = s.id join job_order_bom b on l.job_rule_id = b.job_rule_id where s.product_tmpl_id=%s ',(bom.product_tmpl_id.id,))

            #for rs in self.env.cr.dictfetchall():
                #rule_qty += rs['quantity']
                        
        for mrp in self.job_order_mrp_ids:
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', mrp.bom_id.product_tmpl_id.id )],limit=1)
            vendor_id = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', mrp.bom_id.product_tmpl_id.id )]).name
            if mrp.bom_id.type == 'normal':
                svals = {
                    'product_id': product_id.id,
                    'product_uom_id':product_id.uom_id.id,
                    'product_qty':mrp.quantity,
                    'bom_id':mrp.bom_id.id,
                    'origin':self.sale_id.name,
                    #'orderpoint_id':self.sale_id.id,
                    'procurement_group_id':self.sale_id.id,
                    'job_order_id': self.id,
                    'ref_sale_id':self.sale_id.id,
                }
                semi_production_id = self.env['mrp.production'].create(svals)
                self.env.cr.commit()

            elif mrp.bom_id.type == 'subcontract':
                vals = {
                    'partner_id': 1,
                    'group_id': self.sale_id.id,
                    'origin': self.sale_id.name,
                    'picking_type_id': picking_type_id.id,
                    'date_order': self.date_order,
                }
                purchase_id = self.env['purchase.order'].create(vals)
                self.env.cr.commit()
                line_val = {
                    'name':product_id.name,
                    'order_id':purchase_id.id,
                    'product_id':product_id.id,
                    'product_uom':product_id.uom_po_id.id,
                    'product_qty':mrp.quantity,
                    'price_unit':1,
                    'date_planned': self.date_order,
                }
                purchase_line_id = self.env['purchase.order.line'].create(line_val)
                self.env.cr.commit()
       
        raise Warning(_(rule_qty))
        
    def compute_job(self):
        bom_ids = []
        all_boms = []
        self.job_order_lines.unlink()
        self.job_order_mrp_ids.unlink()
        job_order_line = self.env['job.order.line']
        for job in self:
            for sale in job.job_order_sale_lines:
                if not (sale.bom_id in bom_ids):
                    bom_ids.append(sale.bom_id)
                #sale = sale.id
                for rule in job.struct_id.rule_ids:
                    result_dict = {
                        'job_order_id':job.id,
                        'job_sale_line_id':sale.id,
                        'name': sale.product_tmpl_id.name + '-' + rule.name,
                        'code':rule.code,
                        'sequence':rule.sequence,
                        'category_id':rule.category_id.id,
                        'job_rule_id':rule.id,
                        'line_desc':rule.name,
                        'quantity':sale.product_uom_qty,
                    }
                    job_order_line.create(result_dict)
        #self.state = 'planned'
        for boms in bom_ids:
            all_boms += boms._recursive_boms()
        
        bom_line = self.env['job.order.mrp']
        #bom_line = self.env['job.order.mrp'].search([('bom_id', 'not in', [bom_ids])])
        for bom in all_boms:
            val = {
                'job_order_id':self.id,
                'bom_id':bom,
            }
            bom_line.create(val)
         
        for b in bom_ids:
            bom_line.search([('bom_id', '=', b.id)]).unlink()
    
    def generate_sale_lines(self):
        vals = {}
        self.job_order_sale_lines.unlink()
        job_sale_line = self.env['job.order.sale.line']
        for line in self.sale_id.order_line:
            if line.product_uom_qty:
                vals = {
                    'job_order_id': self.id,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty' : line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'sale_line_id': line.id,
                    'struct_id': self.struct_id.id,
                    #'bom_id': self._get_bom_id(line.product_id.product_tmpl_id),
                    'bom_id': line.product_id.product_tmpl_id.bom_ids.id,
                }
                job_sale_line.create(vals)
                
        self.state = 'confirmed'
    
    def _compute_details_by_component_category(self):
        for job in self:
            job.details_by_component_category = job.mapped('job_order_lines').filtered(lambda line: line.category_id)
    
class JobOrderSaleLine(models.Model):
    _name = 'job.order.sale.line'
    _description = 'Job Order Sale Line'
    _order = 'id desc'
    
    @api.model
    def _get_default_uom(self):
        return self.product_tmpl_id.uom_id
    
    job_order_id = fields.Many2one('job.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    
    sale_line_id = fields.Many2one('sale.order.line', string='Order Line', required=True, index=True)
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        domain="[('type', 'in', ['product', 'consu'])]", required=False)
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.")
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',change_default=True, default=_get_default_uom)
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    struct_id = fields.Many2one('job.order.structure', string='Structure', readonly=True)
    bom_id = fields.Many2one('mrp.bom', string='BOM')
    
    @api.depends('product_uom_qty')
    def _get_secondary_qty(self):
        """
        Compute the total Quantity Weight of the SO Line.
        """
        for line in self:
            line.secondary_qty = line.product_uom_qty * line.product_id.product_tmpl_id.secondary_unit_qty
            line.secondary_uom = line.product_id.product_tmpl_id.secondary_uom_id.name
    
    
class JobOrderLine(models.Model):
    _name = 'job.order.line'
    _inherit = 'job.order.rule'
    _description = 'Job Order Line'
    _order = 'sequence'
    
    job_order_id = fields.Many2one('job.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    job_sale_line_id = fields.Many2one('job.order.sale.line', string='Job Order Sale Line', required=False, index=True)
    #product_tmpl_id = fields.
    product_tmpl_id = fields.Many2one('product.template', related='job_sale_line_id.product_tmpl_id', string='Product', store=True, readonly=True)
    
    job_rule_id = fields.Many2one('job.order.rule', 'Job Rule',required=True)
    line_desc = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', required=True, digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    
    total = fields.Float(compute='_compute_total', string='Total', store=True)

    @api.depends('quantity')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity)
            
class JobOrderBOM(models.Model):
    _name = 'job.order.mrp'
    _description = 'Jor Order Production'
    
    #job_order_id = fields.Many2one('Job.order', string='Job Order Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    job_order_id = fields.Many2one('job.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    bom_id = fields.Many2one('mrp.bom', string='BOM',readonly=True)
    bom_type = fields.Selection('mrp.bom', related='bom_id.type',string='Type',readonly=True, store=True)
    quantity = fields.Float(string='Quantity')
    
    
    def write(self, values):
        return super(JobOrderBOM, self).write(values)
    
    def create(self, values):
        return super(JobOrderBOM, self).create(values)
    
    #@api.depends('job_rule_id')
    def _compute_quantity(self):
        
        test = '0'
        #job_sale_lines = self.env['job.order.sale.line'].search([('job_order_id', '=', rs.job_order_id.id),('product_tmpl_id', '=', line.product_tmpl_id.id)])

        for rs in self:
            rule_qty = 0
            job_order_lines = self.env['job.order.line'].search([('job_order_id', '=', rs.job_order_id.id),('job_rule_id', '=', rs.job_rule_id.id)])
            for line in job_order_lines:
                rule_qty += line.quantity
                #for sale in job_sale_lines:
                    #rule_qty += line.quantity
                    #if line.job_rule_id.id == rs.job_rule_id.id:
                        #if sale.product_tmpl_id.id == line.job_sale_line_id.product_tmpl_id.id:
                            #rule_qty += line.quantity
                        #rule_qty += 0
                            #rule_qty += line.quantity
            rs.quantity = rule_qty
        #raise Warning(_(self.bom_id.product_tmpl_id.id))