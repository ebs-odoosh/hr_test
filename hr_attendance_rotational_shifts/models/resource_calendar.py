# -*- coding: utf-8 -*-
"""  Resource Calendar Attendance Shift Removing"""

from odoo import api, fields, models


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    attendance_ids = fields.One2many(ondelete='cascade',)


class ResourceCalendarAttendance(models.Model):

    _inherit = 'resource.calendar.attendance'

    single_assign_id = fields.Many2one(
        comodel_name="hr.employee.single.shift.assign",
        ondelete='cascade',
    )
    multiple_assign_id = fields.Many2one(
        comodel_name="hr.employee.multiple.shift.assign",
        ondelete='cascade',
    )
