# -*- coding: utf-8 -*-
{
    'name': "Hr Organization Chart",
    'summary': "Organization's Hierarchy Chart Of Employees & Departments",
    'author': "Omnia Sameh<omniaawahab92@gmail.com>",
    'category': 'Human Resources',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'depends': ['hr'],
    'data': [
        'views/web_templates.xml',
        'views/org_chart_views.xml',
    ],
    'qweb': [
        'static/src/xml/hr_organization_chart.xml',
    ],
    'demo': [
        'demo/hr_department.xml',
        'demo/hr_employee.xml',
    ],
    'installable': True,
    'application': True,
}
