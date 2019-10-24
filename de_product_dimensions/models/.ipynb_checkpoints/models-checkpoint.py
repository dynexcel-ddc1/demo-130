# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.template'

    weight_sm = fields.Integer(string='GSM')
    width = fields.Integer(string='Width')
    length = fields.Integer(string='Length')
    height = fields.Integer(string='Height')
    weight1 = fields.Integer(string='Weight')
    
    
    