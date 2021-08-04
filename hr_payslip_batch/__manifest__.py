# -*- coding: utf-8 -*-
{
    'name': "Hr Payslip Batch",
    'summary': """Generate Payslip Batch From Attendance Sheet Batch.""",
    'author': "Omnia Sameh, ITSS <https://www.itss-c.com>",
    'category': 'HR',
    'version': '12.0.1.0.0',
    'depends': [
        'base',
        'hr_payroll',
        'att_sheet_batch',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_sheet_batch_view.xml',
        'views/hr_payslip_run_views.xml'
    ],
}
