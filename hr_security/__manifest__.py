# -*- coding: utf-8 -*-
{
    'name': "Fakhama HR Security",
    'summary': """ Fakhama HR Security Rules. """,
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    'category': 'HR',
    'version': '12.0.1.0.0',
    'depends': ['hr', 'hr_holidays', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_holidays_security.xml',
        'security/hr_attendance_security.xml',
        'security/hr_employee.xml',
    ]
}
