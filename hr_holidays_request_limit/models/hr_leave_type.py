# -*- coding: utf-8 -*-
"""HR Holidays Request Limit"""

from odoo.tools.float_utils import float_round
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LeaveType(models.Model):
    _inherit = "hr.leave.type"

    is_permission = fields.Boolean()
    enable_max_requests_per_week = fields.Boolean()
    max_requests_per_week = fields.Integer()
    week_start = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ])
    enable_max_requests_per_month = fields.Boolean()
    max_requests_per_month = fields.Integer()
    month_start = fields.Integer()
    enable_max_hours_per_request = fields.Boolean()
    max_hours_per_request = fields.Integer()

    enable_max_requests_per_day = fields.Boolean()
    max_requests_per_day = fields.Integer()

    @api.onchange('is_permission')
    def _onchange_is_permission(self):
        if self.is_permission:
            self.request_unit = 'hour'

    @api.constrains('is_permission')
    def _check_single_permission_type(self):
        """only one holiday type is a permission."""
        records = self.search([('is_permission', '=', True)])
        if len(records) > 1:
            raise ValidationError(_("Can't create multiple permission holiday type."))
        if self.is_permission and self.request_unit != 'hour':
            raise ValidationError(_("Permission holiday type must be taken in hours."))

    @api.multi
    def get_days(self, employee_id, day):
        # need to use `dict` constructor to create a dict per id
        result = dict(
            (id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

        requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        leave_day = day and day or fields.Date.today()
        for request in requests:
            if request.holiday_status_id.is_permission and not (request.allocation_date_from
                                                                and request.allocation_date_to):
                continue
            status_dict = result[request.holiday_status_id.id]

            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                        if request.leave_type_request_unit == 'hour'
                                                        else request.number_of_days)
            if request.state in ['validate', 'validate1']:


                if request.holiday_status_id.is_permission and request.allocation_date_from \
                        and request.allocation_date_to:
                    if not (request.allocation_date_from <= leave_day <= request.allocation_date_to):
                        continue
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)

        for allocation in allocations.sudo():
            if allocation.holiday_status_id.is_permission and not (allocation.allocation_date_from
                                                                   and allocation.allocation_date_to):
                continue
            status_dict = result[allocation.holiday_status_id.id]
            if allocation.state in ['validate', 'validate1']:
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible

                if allocation.holiday_status_id.is_permission and allocation.allocation_date_from \
                        and allocation.allocation_date_to:
                    if not (allocation.allocation_date_from <= leave_day <= allocation.allocation_date_to):
                        continue
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                            if allocation.type_request_unit == 'hour'
                                                            else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                              if allocation.type_request_unit == 'hour'
                                              else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                    if allocation.type_request_unit == 'hour'
                                                    else allocation.number_of_days)
        return result

    @api.multi
    def _compute_leaves(self):
        data_days = {}
        employee_id = self._get_contextual_employee_id()
        day = 'date' in self._context and self._context['date']

        if employee_id:
            data_days = self.get_days(employee_id, day)

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
