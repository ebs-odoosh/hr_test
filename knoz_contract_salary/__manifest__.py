# -*- coding: utf-8 -*-
{
    'name': "knoz contract salary",

    'summary': """
        add salary details in contact , wage will be sum of all the salary lines 
        and the salary lines can be added to salary computation in payslip """,

    'description': """
        add salary details in contact , wage will be sum of all the salary lines
    """,

    'author': "Islam Abdelmaaboud",
    'website': "http://www.itss-c.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/hr_contract_salary_line.xml',


    ],

}