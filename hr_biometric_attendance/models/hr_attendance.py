import csv
from datetime import datetime, timedelta
import base64


from odoo import models, fields, api,_
from odoo.exceptions import UserError,ValidationError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"
from odoo import http


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.one
    def fix_register(self):
        self.write({'state': 'right'})


    state = fields.Selection(
        selection=[('fix', 'Fix'), ('right', 'Right')],
        default='right',
        help='The user did not register an input '
             'or an output in the correct order, '
             'then the system proposed one or more regiters to fix the problem '
             'but you must review the created register due '
             'because of hour could be not correct')

    check_in_machine_id = fields.Many2one(comodel_name="biometric.machine")
    check_out_machine_id = fields.Many2one(comodel_name="biometric.machine")
    manual_in_id = fields.Many2one(comodel_name="manual.attendance")
    manual_out_id = fields.Many2one(comodel_name="manual.attendance")



    @api.model
    def create(self,vals):
        is_from_machine = self._context.get('machine',False)
        if not is_from_machine:
            if 'check_in' in vals:
                manual_attend = self.env['manual.attendance'].search(
                    [('attendance_time', '=', vals['check_in']), ('employee_id', '=', vals['employee_id'])])
                manual_attend.sudo().unlink()
                manual_in = self.env['manual.attendance'].create({
                    'attendance_time': vals['check_in'],
                    'type': 'check_in',
                    'employee_id': vals['employee_id'],
                })
                vals['manual_in_id'] = manual_in.id

            if 'check_out' in vals:
                manual_attend = self.env['manual.attendance'].search(
                    [('attendance_time', '=', vals['check_out']), ('employee_id', '=', vals['employee_id'])])
                manual_attend.sudo().unlink()
                manual_out = self.env['manual.attendance'].create({
                    'attendance_time': vals['check_out'],
                    'type': 'check_out',
                    'employee_id': vals['employee_id'],
                })
                vals['manual_out_id'] = manual_out.id
        rec  = super(HrAttendance,self).create(vals)
        return rec

    @api.multi
    def write(self,vals):
        is_from_machine = self._context.get('machine',False)
        if not is_from_machine:
            if 'check_in' in vals:
                if self.manual_in_id:
                    self.manual_in_id.write({'attendance_time': vals.get('check_in')})
                else:
                    manual_in = self.env['manual.attendance'].create({
                        'attendance_time': vals.get('check_in'),
                        'type': 'check_in',
                        'employee_id': self.employee_id.id,
                    })
                    vals['manual_in_id'] = manual_in.id

            if 'check_out' in vals:
                if self.manual_out_id:
                    self.manual_out_id.write({'attendance_time': vals.get('check_out')})
                else:
                    manual_out = self.env['manual.attendance'].create({
                        'attendance_time': vals.get('check_out'),
                        'type': 'check_out',
                        'employee_id': self.employee_id.id,
                    })
                    vals['manual_out_id'] = manual_out.id

        return super(HrAttendance,self).write(vals)


class ManualAttendance(models.Model):
    _name = 'manual.attendance'

    employee_id = fields.Many2one(comodel_name="hr.employee")
    attendance_time = fields.Datetime()
    type = fields.Selection( selection=[('check_in', 'Check In'), ('check_out', 'Check Out')])
