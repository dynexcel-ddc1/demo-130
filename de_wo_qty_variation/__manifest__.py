{
    'name' : 'Work Order Quantity Variation',
    'version' : '13.0.0.0',
    'author' : 'Dynexcel',
    'website' : 'http://www.dynexcel.co',
    'category' : 'MRP',
    'description' : """
        Enterprise
        This module will change the default behavior of the current quantity of work orders. 
        Work Order will receive the produced quantity from previous subsequent work order and so on. 
    """,
    'depends' : ['mrp'],
    'demo' : [],
    'data' : [
        'views/mrp_production_view.xml'
    ],
    'installable' : True,
}

