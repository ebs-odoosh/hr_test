# -*- coding: utf-8 -*-
{
    'name': "knoz_contract",

    'summary': """
        Renew Employee Contract , get all versions of the Contract and Track visibility for some fields """,

    'description': """
        Renew Employee Contract , get all versions of the Contract and Track visibility for some fields
    """,

    'author': "Islam Abdelmaaboud",
    'website': "http://www.itss-c.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}