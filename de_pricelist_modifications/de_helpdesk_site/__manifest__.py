# -*- coding: utf-8 -*-
{
    'name': "Helpdesk Site",

    'summary': """
        Helpdesk Service Site Details
        """,

    'description': """
        Service site detail of customer
    """,

    'author': "Dynexcel",
    'website': "http://www.dynexcel.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'After-Sales',
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base','de_helpdesk','product','stock','de_helpdesk_repair_warranty','portal',],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/helpdesk_site_views.xml',
        'views/helpdesk_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
