# -*- coding: utf-8 -*-
{
    'name': 'Hr Employee Tasks',
    'version': '12.0.1.0.0',
    'summary': 'Assign Tasks With Details To Employees',
    'author': 'ITSS, Omnia Sameh',
    'website': 'https://itss-c.com',
    'category': 'HR',
    'depends': ['hr', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_employee.xml',
        'security/hr_employee_task.xml',
        'data/hr_employee_task.xml',
        'views/hr_employee_task.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
}
