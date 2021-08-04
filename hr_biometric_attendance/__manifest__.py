# -*- coding: utf-8 -*-
{
    'name': "Biometric Attendance Download",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Eng.Ramadan Khalil",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_attendance',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_attendance.xml',
        'views/biometric_view.xml',
        'views/manual_attendance.xml',
        'wizard/schedule_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
