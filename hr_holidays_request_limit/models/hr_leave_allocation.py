# -*- coding: utf-8 -*-
""" init object """

from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError
import logging

LOGGER = logging.getLogger(__name__)


class Allocation(models.Model):

    _inherit = 'hr.leave.allocation'

    allocation_date_from = fields.Date()
    allocation_date_to = fields.Date()
    is_permission = fields.Boolean(related='holiday_status_id.is_permission')

    @api.constrains('allocation_date_from', 'allocation_date_to')
    def _check_allocation_dates(self):
        if any(self.filtered(lambda record: record.allocation_date_from > record.allocation_date_to)):
            raise ValidationError(_("Error! 'Allocation Date From' must be before 'Allocation Date To'."))
        if self.allocation_date_from and self.allocation_date_to and self.employee_id:
            domain = [
                ('allocation_date_from', '<=', self.allocation_date_to),
                ('allocation_date_to', '>=', self.allocation_date_from),
                ('employee_id', '=', self.employee_id.id),
                ('id', '!=', self.id),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nallocations = self.search_count(domain)
            if nallocations:
                raise ValidationError(_('You can not have 2 allocations that overlap on dates'))

    @api.multi
    def _prepare_holiday_values(self, employee):
        values = super(Allocation, self)._prepare_holiday_values(employee)
        values.update(
            {

                "allocation_date_from": self.allocation_date_from,
                "allocation_date_to": self.allocation_date_to,
            }
        )
        return values
