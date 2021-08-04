# -*- coding: utf-8 -*-
"""HR Holidays Request Limit"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, date
from dateutil import relativedelta
from odoo.tools import float_compare

import logging

LOGGER = logging.getLogger(__name__)


class Leave(models.Model):
    _inherit = 'hr.leave'

    allocation_date_from = fields.Date(compute='_compute_matched_allocation', )
    allocation_date_to = fields.Date(compute='_compute_matched_allocation', )

    @api.multi
    @api.depends('employee_id', 'holiday_status_id', 'holiday_status_id.is_permission', 'request_date_from')
    def _compute_matched_allocation(self):
        for holiday in self:
            if holiday.request_date_from and holiday.holiday_status_id.is_permission and holiday.employee_id:
                allocations = self.env['hr.leave.allocation'].search([
                    ('holiday_status_id.is_permission', '=', True),
                    ('allocation_date_from', '<=', holiday.request_date_from),
                    ('allocation_date_to', '>=', holiday.request_date_from),
                    ('employee_id', '=', holiday.employee_id.id),
                    ('state', 'in', ['validate', 'validate1'])
                ])
                if allocations:
                    allocation = allocations[0]
                    holiday.allocation_id = allocation
                    holiday.allocation_date_from = allocation.allocation_date_from
                    holiday.allocation_date_to = allocation.allocation_date_to

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
                continue
            leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id, day=holiday.request_date_from)[holiday.holiday_status_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
                    float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please also check the leaves waiting for validation.'))

    @api.onchange('holiday_status_id', 'holiday_status_id.is_permission')
    def onchange_holiday_status(self):
        for holiday in self:
            if holiday.holiday_status_id.is_permission:
                holiday.update({'request_unit_hours': True})

    @api.multi
    def _check_leave_type_limit(self):
        for holiday in self:
            emp = holiday.employee_id
            date_from = fields.Date.from_string(holiday.date_from)
            leave_type = holiday.holiday_status_id
            if leave_type.enable_max_requests_per_week:
                week_start = int(leave_type.week_start)
                if date_from.weekday() > week_start:
                    start = date_from - timedelta(days=(date_from.weekday() - week_start))
                else:
                    start = date_from - timedelta(days=7 - (week_start - date_from.weekday()))
                end = start + timedelta(days=7)
                start = str(start)
                end = str(end)
                leaves_count = self.search_count(
                    [('id', '!=', holiday.id),
                     ('holiday_status_id', '=', leave_type.id),
                     ('state', 'not in', ('cancel', 'refuse', 'draft')),
                     ('date_from', '>=', start),
                     ('date_from', '<=', end),
                     ('employee_id', '=', emp.id)])
                if leaves_count >= leave_type.max_requests_per_week:
                    raise UserError(_("Max Requests Per Week  is %s Requests" %
                                      (str(leave_type.max_requests_per_week))))

            if leave_type.enable_max_requests_per_month:
                month_start = leave_type.month_start
                start = False
                end = False
                if month_start <= int(date_from.day):
                    start = date(date_from.year, date_from.month, month_start)
                    end = start + relativedelta.relativedelta(months=1)
                else:
                    start = date(date_from.year, date_from.month, month_start) - relativedelta.relativedelta(months=1)
                    end = date(date_from.year, date_from.month, month_start)

                start = str(start)
                end = str(end)
                leaves_nu = self.search_count(
                    [('id', '!=', holiday.id),
                     ('holiday_status_id', '=', holiday.holiday_status_id.id),
                     ('state', 'not in', ('cancel', 'refuse', 'draft')),
                     ('date_from', '>=', start),
                     ('date_from', '<=', end),
                     ('employee_id', '=', holiday.employee_id.id)])
                if leaves_nu > leave_type.max_requests_per_month:
                    raise UserError(_("Max Request Per Month  is %s Requests" %
                                      (str(leave_type.max_requests_per_month))))
            if leave_type.max_hours_per_request and leave_type.max_hours_per_request < holiday.number_of_hours_display:
                raise UserError(_("Max Hours Per Permission is %s Hours" % (str(leave_type.max_hours_per_request))))

            if leave_type.max_requests_per_day:
                leaves_count = self.search_count(
                    [('id', '!=', holiday.id),
                     ('holiday_status_id', '=', holiday.holiday_status_id.id),
                     ('state', 'not in', ('cancel', 'refuse', 'draft')),
                     ('request_date_from', '=', holiday.request_date_from),
                     ('employee_id', '=', holiday.employee_id.id)])

                if leaves_count >= leave_type.max_requests_per_day:
                    raise UserError(_("Max Requests Per Day  is %s Requests" % (str(leave_type.max_requests_per_day))))

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        super(Leave, self)._check_date()
        self._check_leave_type_limit()
