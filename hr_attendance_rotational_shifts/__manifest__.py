# -*- coding: utf-8 -*-
{
    'name': "Hr Employee Rotational Shifts",
    'summary': """ Assign Rotational Shifts To Employees Calendar Per Month. """,
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    'category': 'HR',
    'version': '1.0.0',
    'depends': ['hr_attendance_sheet'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_weekend.xml',
        'views/web_templates.xml',
        'views/resource_calendar_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_shift.xml',
        'views/hr_employee_single_shift_assign.xml',
        'views/hr_employee_multiple_shift_assign.xml',
        'views/hr_employee_views.xml',
        'views/report_hr_employee_shifts.xml',
        'views/hr_employee_reports.xml',
        'wizard/hr_employee_shifts_report_wizard.xml',
    ],
    'demo': ['demo/hr_employee_shift.xml'],
}
