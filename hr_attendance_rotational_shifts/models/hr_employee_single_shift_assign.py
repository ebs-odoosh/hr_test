# -*- coding: utf-8 -*-
""" Hr Employee Single Shift Assigning  """

from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

DAY_OF_WEEK = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday')
]


class HrEmployeeSingleShiftAssign(models.Model):
    """Hr Employee Single Shift Assign Model
    
    This model assign single shift to employees with excluding days
    as weekend days.
    """

    _name = 'hr.employee.single.shift.assign'

    name = fields.Char(
        Translate=True,
    )

    state = fields.Selection(
        string="Status",
        default="draft",
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ],
    )

    weekend_ids = fields.Many2many(
        comodel_name='hr.weekend',
        string='Weekend Days'
    )

    department_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='employee_department_shift_assign_rel',
        column1='assign_id',
        column2='dep_id',
        string='Departments',
    )
    category_ids = fields.Many2many(
        comodel_name='hr.employee.category',
        relation='employee_category_shift_assign_rel',
        column1='assign_id',
        column2='category_id',
        string='Tags'
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="employee_single_shift_assign_rel",
        column1="assign_id",
        column2="employee_id",
        string="Employees",
    )
    shift_id = fields.Many2one(
        comodel_name="hr.employee.shift",
    )
    time_from = fields.Float(related='shift_id.time_from')
    time_to = fields.Float(related='shift_id.time_to')
    date_from = fields.Date(
        default=fields.Date.today(),
    )
    date_to = fields.Date(
        default=fields.Date.today(),
    )
    dates_diff = fields.Integer(compute='_compute_dates_difference')
    flexible_hours = fields.Float(related="shift_id.flexible_hours")

    assign_flexible_hour = fields.Boolean()

    @api.onchange('department_ids', 'category_ids')
    def _onchange_department_emp_categories(self):
        """Change employee domain with changing the department and
        the employees' categories """
        domain = []
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.category_ids:
            domain.append(('category_ids', 'in', self.category_ids.ids))
        return {'domain': {'employee_ids': domain}}

    @api.constrains('date_from', 'date_to')
    def _check_assign_dates(self):
        if any(self.filtered(lambda record: record.date_from > record.date_to)):
            raise ValidationError(_("Error! 'Date From' must be before 'Date To'."))
        today = fields.Date.from_string(fields.Date.today())
        date_from = fields.Date.from_string(self.date_from)
        if date_from < today and (today - date_from).days > 60:
            raise ValidationError(_("Error! you can assign previous shifts only in"
                                    " the last 60 days."))
        if (self.shift_id.time_from >= self.shift_id.time_to) and (self.date_from == self.date_to):
            raise ValidationError(_("Error! 'Date To' must be greater than 'Date From'"
                                    " , the shift exceeds the 'Date From'."))

    @api.multi
    @api.depends('date_from', 'date_to')
    def _compute_dates_difference(self):
        for record in self:
            if record.date_from and record.date_to:
                date_from = fields.Date.from_string(record.date_from)
                date_to = fields.Date.from_string(record.date_to)
                record.dates_diff = (date_to - date_from).days

    def action_confirm_shift_assign(self):
        self.state = 'confirmed'
        employees = self.employee_ids
        if not employees:
            domain = []
            if self.department_ids:
                domain.append(('department_id', 'in', self.department_ids.ids))
            if self.category_ids:
                domain.append(('category_ids', 'in', self.category_ids.ids))
            employees = self.env['hr.employee'].search(domain)
        weekend_days = self.weekend_ids.mapped('code')
        self._create_schedule_lines(employees, self.date_from, self.date_to,
                                    self.shift_id, weekend_days)

    def _create_month_calendar(self, emp, start_date):
        """ Create month shifts schedule without the default Odoo shifts. """
        res_calendar = self.env['resource.calendar']. \
            create({'name': _('Schedule For ') + start_date.strftime("%B")})
        res_calendar.write({'attendance_ids': [(5,)]})
        last_day = \
            calendar.monthrange(start_date.year, start_date.month)[1]
        last_day_date = datetime(start_date.year, start_date.month,
                                 last_day).date()
        first_day_date = datetime(start_date.year, start_date.month, 1).date()
        emp.write({'employee_shift_schedule_ids': [(0, 0, {
            'resource_calendar_id': res_calendar.id,
            'date_from': first_day_date,
            'date_to': last_day_date
        })]})
        return res_calendar

    def _create_schedule_lines(self, employees, date_from, date_to, shift_id, weekend_days):
        """This function executed when the record confirmed to assign
        the required shift to the employee(s), it divides the dates
        interval per month and create schedule line for each
        employee if there is no one for the required month.
        """
        date_from = fields.Date.from_string(date_from)
        date_to = fields.Date.from_string(date_to)
        dates = (date_from.month == date_to.month or (date_to.month != date_from.month and \
                (date_to - date_from).days == 1 and \
                shift_id.time_to <= shift_id.time_from)) and [[date_from, date_to]] or []
        if not dates:
            while date_to.month != date_from.month:
                last_day = calendar.monthrange(date_from.year, date_from.month)[1]
                last_day_date = datetime(date_from.year, date_from.month, last_day).date()
                dates.append([date_from, last_day_date])
                date_from = last_day_date + relativedelta(days=1)
                if date_from.month == date_to.month:
                    dates.append([date_from, date_to])
        for emp in employees:
            for date_interval in dates:
                start_date = date_interval[0]
                end_date = date_interval[1]
                shift = emp.employee_shift_schedule_ids. \
                    filtered(lambda record: fields.Date.from_string(record.date_from) <= start_date <=
                             fields.Date.from_string(record.date_to)
                             # and int(fields.Date.from_string(record.date_from).strftime("%m")) == start_date.month
                             )
                res_calendar = shift and shift.resource_calendar_id or \
                               self._create_month_calendar(emp, start_date)
                if self.assign_flexible_hour:
                    res_calendar.flexible_hours = shift_id.flexible_hours
                diff = (end_date - start_date).days
                if diff > 6:
                    for i in range(0, 7):
                        if i not in weekend_days:
                            week_day = [list(day)[1] for day in DAY_OF_WEEK
                                        if i == int(list(day)[0])][0]
                            res_calendar.write({
                                'attendance_ids': [(0, 0, {
                                    'name': week_day,
                                    'dayofweek': str(i),
                                    'date_from': start_date,
                                    'date_to': end_date,
                                    'hour_from': shift_id.time_from,
                                    'hour_to': shift_id.time_to,
                                    'single_assign_id': self.id,
                                })]
                            })
                else:
                    if shift_id.time_to <= shift_id.time_from:
                        end_date = end_date - relativedelta(days=1)
                    while end_date >= start_date:
                        day_week_nu = start_date.weekday()
                        # weekend_days = self.weekend_ids.mapped('code')
                        if day_week_nu not in weekend_days:
                            day_week = [list(day)[1] for day in DAY_OF_WEEK
                                        if day_week_nu == int(list(day)[0])][0]
                            shift_end_date = start_date + relativedelta(days=1) \
                                if shift_id.time_to < shift_id.time_from else start_date
                            res_calendar.write({
                                'attendance_ids': [(0, 0, {
                                    'name': day_week,
                                    'dayofweek': str(day_week_nu),
                                    'date_from': start_date,
                                    'date_to': shift_end_date,
                                    'hour_from': shift_id.time_from,
                                    'hour_to': shift_id.time_to,
                                    'single_assign_id': self.id,
                                })]
                            })
                        start_date = start_date + relativedelta(days=1)

    @api.multi
    def unlink(self):
        for record in self:
            attendance_line = self.env['resource.calendar.attendance'].search([('single_assign_id', '=', record.id)])
            calendar = attendance_line.mapped('calendar_id')
            calendar = calendar and calendar[0]
            last = False
            if calendar and len(calendar.attendance_ids) == len(attendance_line):
                last = True
            res = super(HrEmployeeSingleShiftAssign, self).unlink()
            if last:
                calendar.unlink()
            return res
