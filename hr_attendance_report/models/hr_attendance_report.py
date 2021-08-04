# -*- coding: utf-8 -*-
"""HR Attendance Report"""

import pytz
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import ValidationError


class AttendanceReport(models.Model):
    """HR Attendance Report Model

    Attendance report for daily attendance status.
    """
    _name = 'hr.attendance.report'

    name = fields.Char(compute='_compute_name')

    department_ids = fields.Many2many(
        comodel_name='hr.department',
        string='Departments',
    )
    category_ids = fields.Many2many(
        comodel_name='hr.employee.category',
        string='Tags'
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Employees",
    )

    date_from = fields.Date(
        default=fields.Date.today(),
        required=True,
    )
    date_to = fields.Date(
        default=fields.Date.today(),
        required=True,
    )
    report_line_ids = fields.One2many(
        comodel_name="hr.attendance.report.line",
        inverse_name="report_id",
        string="Attendance Lines",
    )
    state = fields.Selection(
        string="Status",
        default="draft",
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ],
    )

    @api.multi
    @api.depends('department_ids', 'date_from', 'date_to')
    def _compute_name(self):
        for record in self:
            if record.department_ids and record.date_from:
                date_from = fields.Date.from_string(record.date_from)
                record.name = _('Attendance Report of %s Department(s) for %s ') % \
                               (', '.join([dep.name for dep in record.department_ids]),
                                date_from.strftime('%d %B-%Y'))

    @api.constrains('date_from', 'date_to')
    def _check_assign_dates(self):
        if any(self.filtered(lambda record: record.date_from > record.date_to)):
            raise ValidationError(_("Error! 'Date From' must be before 'Date To'."))

    @api.onchange('department_ids', 'category_ids')
    def _onchange_department_emp_categories(self):
        """Change employee domain with changing the department and
        the employees' categories """
        self.employee_ids = False
        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.category_ids:
            domain.append(('category_ids', 'in', self.category_ids.ids))
        return {'domain': {'employee_ids': domain}}

    def _create_employees_attendance_sheets(self):
        att_sheets = self.env['attendance.sheet']
        employees = self.employee_ids
        from_date = self.date_from
        to_date = self.date_to
        if not employees:
            domain = []
            if self.department_ids:
                domain.append(('department_id', 'in', self.department_ids.ids))
            if self.category_ids:
                domain.append(('category_ids', 'in', self.category_ids.ids))

            employees = self.env['hr.employee'].search(domain)
        if not employees:
            raise ValidationError(_("There aren't employees in the selected department(s) "
                                    "/ tags."))
        for employee in employees:
            contract_ids = self.env['hr.payslip'].get_contract(employee, from_date, to_date)
            if not contract_ids:
                raise ValidationError(_("There is no  Running contracts for :%s " % employee.name))
            att_data = self.env['attendance.sheet'].onchange_employee_id(from_date, to_date,
                                                                         employee.id)
            res = {
                'employee_id': employee.id,
                'date_from': from_date,
                'date_to': to_date,
                'att_policy_id': att_data['value'].get('att_policy_id')
            }
            att_sheet = self.env['attendance.sheet'].create(res)
            today_dt = str(
                fields.Datetime.from_string(fields.Datetime.now()).replace(hour=0, minute=0,
                                                                           second=0))
            today_end_dt = str(
                fields.Datetime.from_string(fields.Datetime.now()).replace(hour=23, minute=59))

            attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', employee.id),
                 ('check_in', '>=', today_dt),
                 ('check_in', '<', today_end_dt),
                 ('check_out', '=', False)])

            if len(attendance) == 1:
                tz = pytz.timezone(att_sheet.env.user.tz)

                attendance.check_out = pytz.utc.localize(
                    fields.Datetime.from_string(attendance.check_in)). \
                                           astimezone(tz).replace(tzinfo=None) + relativedelta(
                    minute=1)

                # attendance.check_out = fields.Datetime.from_string(attendance.check_in) + relativedelta(minute=1)
            att_sheet.get_attendances()
            if attendance:
                attendance.check_out = False
                sheet_line = [line for line in att_sheet.att_sheet_line_ids if
                              line.date == fields.Date.today()]
                if sheet_line:
                    sheet_line = sheet_line[0]
                    sheet_line.ac_sign_out = False
                    sheet_line.overtime = False
                    sheet_line.diff_time = False
                    sheet_line.worked_hours = False
                    sheet_line.att_status = 'late' if sheet_line.late_in else False
            att_sheets += att_sheet
        return att_sheets

    def action_confirm_attendance_report(self):
        for record in self:
            record.state = 'confirmed'

    def action_generate_attendance_report(self):
        for record in self:
            if record.report_line_ids:
                record.report_line_ids.unlink()
            sheets = self._create_employees_attendance_sheets()
            for sheet in sheets:
                for line in sheet.att_sheet_line_ids:
                    values = {
                        'date': line.date,
                        'day': line.day,
                        'ac_sign_in': line.ac_sign_in,
                        'ac_sign_out': line.ac_sign_out,
                        'pl_sign_in': line.pl_sign_in,
                        'pl_sign_out': line.pl_sign_out,
                        'worked_hours': line.worked_hours,
                        'overtime': line.overtime,
                        'late_in': line.late_in,
                        'status': line.status,
                        'att_status': line.att_status,
                        'note': line.note,
                        'report_id': record.id,
                        'employee_id': sheet.employee_id.id,
                    }
                    self.env['hr.attendance.report.line'].create(values)
            sheets.unlink()


class AttendanceReportLine(models.Model):
    """HR Attendance Report Line Model
    
    Attendance report lines for daily attendance status.
    """
    _name = 'hr.attendance.report.line'

    date = fields.Date("Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True,)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        readonly=True,
    )
    report_id = fields.Many2one(
        comodel_name="hr.attendance.report",
    )
    pl_sign_in = fields.Float("Planned sign in",readonly=True)
    pl_sign_out = fields.Float("Planned sign out",readonly=True)
    worked_hours = fields.Float(readonly=True)
    ac_sign_in = fields.Float("Actual sign in",readonly=True)
    ac_sign_out = fields.Float("Actual sign out",readonly=True)
    overtime = fields.Float(readonly=True)
    late_in = fields.Float(readonly=True)
    diff_time = fields.Float(
        help="Difference between the working time"
        " and attendance time(s) ",
        readonly=True
    )
    note = fields.Text(readonly=True)
    status = fields.Selection(
        selection=[('ab', 'Absence'),
                   ('weekend', 'Week End'),
                   ('ph', 'Public Holiday'),
                   ('leave', 'Leave'), ],
        readonly=True,
    )

    att_status = fields.Selection(string="Att Status",
                                  selection=[('late', 'Late In'), ('diff', 'Early Leave'),
                                             ('over', 'Overtime'),
                                             ('over+late', 'Late In, Overtime'),
                                             ('diff+late', 'Late In, Early Leave'), ],
                                  required=False, readonly=True)
