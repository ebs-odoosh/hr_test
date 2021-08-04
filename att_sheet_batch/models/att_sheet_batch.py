# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2018-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################



import itertools
from lxml import etree
import time
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, AccessError, ValidationError
import babel
from operator import itemgetter
import logging

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class attendance_sheet_batch(models.Model):

    _name = 'attendance.sheet.batch'

    name = fields.Char()
    department_ids = fields.Many2many(
        comodel_name='hr.department',
        string='Departments',
    )
    category_ids = fields.Many2many(
        comodel_name='hr.employee.category',
        relation='employee_category_att_batch_rel',
        column1='batch_id',
        column2='category_id',
        string='Tags'
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="employee_shift_att_batch_rel",
        column1="batch_id",
        column2="employee_id",
        string="Employees",
    )
    date_from = fields.Date(string="From", required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="To", required=True,
                          default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    att_sheet_ids = fields.One2many(comodel_name='attendance.sheet', string='Attendance Sheets',
                                    inverse_name='batch_id')
    payslip_batch_id=fields.Many2one(comodel_name='hr.payslip.run',string='Payslip Batch')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('att_gen', 'Attendance Sheets Generated'),
        ('att_sub', 'Attendance Sheets Submitted'),
        ('done', 'Close')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True, )

    @api.multi
    @api.onchange('department_ids', 'date_from', 'date_to')
    def _onchange_department_dates(self):
        for record in self:
            if record.department_ids and record.date_from:
                date_from = fields.Date.from_string(record.date_from)
                record.name = _('Attendance Batch of %s Department(s) for %s ') % \
                    (', '.join([dep.name for dep in record.department_ids]),
                     date_from.strftime('%B-%Y'))

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

    @api.multi
    def action_done(self):
        for batch in self:
            if batch.state != "att_sub":
                continue
            for sheet in batch.att_sheet_ids:
                if sheet.state == 'confirm':
                    sheet.action_attsheet_approve()
                    sheet.create_payslip_id()
            batch.write({'state': 'done'})

    @api.multi
    def action_att_gen(self):
        return self.write({'state': 'att_gen'})

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
                raise UserError(_("There is no  Running contracts for :%s " % employee.name))
            att_data = self.env['attendance.sheet'].onchange_employee_id(from_date, to_date,
                                                                         employee.id)
            res = {
                'employee_id': employee.id,
                'name': att_data['value'].get('name'),
                'month': att_data['value'].get('month'),
                'year': att_data['value'].get('year'),
                'batch_id': self.id,
                'date_from': from_date,
                'date_to': to_date,
                'att_policy_id': att_data['value'].get('att_policy_id')
            }
            att_sheet = self.env['attendance.sheet'].create(res)
            att_sheet.get_attendances()
            att_sheets += att_sheet

    @api.multi
    def gen_att_sheet(self):
        for batch in self:
            batch._create_employees_attendance_sheets()
            batch.action_att_gen()

    @api.multi
    def submit_att_sheet(self):
        for batch in self:
            if batch.state !="att_gen":
                continue
            for sheet in batch.att_sheet_ids:
                if sheet.state == 'draft':
                    sheet.action_attsheet_confirm()
            batch.write({'state': 'att_sub'})
