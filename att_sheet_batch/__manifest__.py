# -*- coding: utf-8 -*-
{
    'name': "Attendance Sheet Batch By Department",

    'summary': """
       """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Eng.Ramadan Khalil",
    'website': "rkhalil1990@gmail.com",
    'category': 'hr',
    'version': '12.0.1.0.0',

    'depends': ['base','hr_attendance_sheet'],

    'data': [
        'security/ir.model.access.csv',
        'views/att_sheet_batch_view.xml',
        'views/attendance_sheet_view.xml'

    ],
    'demo': [
    ],
}