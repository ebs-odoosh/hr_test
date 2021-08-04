# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"

import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)

from ..zk import ZK

from odoo import api, fields, models

import pytz

class biometric_record(models.Model):
    _name = 'biometric.record'
    _order = "name desc"

    name=fields.Datetime('Time')
    machine=fields.Many2one('biometric.machine','Machine Name')
    state = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')], default='success', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True, )
    note=fields.Char('Notes')

class biometric_log(models.Model):
    _name = 'biometric.log'
    _order = "name desc"
    name=fields.Datetime('Time')
    employee_id=fields.Many2one('hr.employee','Employee')
    machine=fields.Many2one('biometric.machine','Machine Name')
    type= fields.Selection([
        ('in', 'In'),
        ('out', 'Out')], default='in')




class biometric_machine(models.Model):
    _name = 'biometric.machine'

    @api.model
    def _cron_att_download(self):
        print("iam in crone method")
        # for mc in self.search([('state', '=', 'active')]):
        for mc in self.search([]):
            mc.download_attendance()

    @property
    def min_time(self):
        # Get min time
        if self.interval_min == 'sec':
            min_time = datetime.timedelta(seconds=self.time_interval_min)
        elif self.interval_min == 'min':
            min_time = datetime.timedelta(minutes=self.time_interval_min)
        elif self.interval_min == 'hour':
            min_time = datetime.timedelta(hours=self.time_interval_min)
        else:
            min_time = datetime.timedelta(days=self.time_interval_min)
        return min_time

    @property
    def max_time(self):
        # Get min time
        if self.interval_max == 'sec':
            max_time = datetime.timedelta(seconds=self.time_interval_max)
        elif self.interval_max == 'min':
            max_time = datetime.timedelta(minutes=self.time_interval_max)
        elif self.interval_max == 'hour':
            max_time = datetime.timedelta(hours=self.time_interval_max)
        else:
            max_time = datetime.timedelta(days=self.time_interval_max)
        return max_time

    @api.model
    def _tz_get(self):
        # Copied from base model
        return [
            (tz, tz) for tz in
            sorted(
                pytz.all_timezones,
                key=lambda tz: tz if not
                tz.startswith('Etc/') else '_')]

    name = fields.Char('Name')
    ip_address = fields.Char('Ip address')
    port = fields.Integer('Port')
    sequence = fields.Integer('Sequence')
    timezone = fields.Selection(
        _tz_get, 'Timezone', size=64,
        help='Device timezone',
    )
    log_ids = fields.One2many(comodel_name="biometric.record", inverse_name="machine", string="Log", required=False, )
    time_interval_min = fields.Integer(
        'Min time',
        help='Min allowed time  between two registers')
    interval_min = fields.Selection(
        [('sec', 'Sec(s)'), ('min', 'Min(s)'),
         ('hour', 'Hour(s)'), ('days', 'Day(s)'), ],
        'Min allowed time', help='Min allowed time between two registers', )
    time_interval_max = fields.Integer(
        'Max time',
        help='Max allowed time  between two registers', )
    interval_max = fields.Selection(
        [('sec', 'Sec(s)'), ('min', 'Min(s)'),
         ('hour', 'Hour(s)'), ('days', 'Day(s)'), ],
        'Max allowed time', help='Max allowed time between two registers', )
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'InActive')], default='inactive', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True, )
    last_connected_time = fields.Datetime(string="Last Connected Time",copy=False)
    last_connected_days = fields.Integer(default=0,compute='compute_last_connected_days')


    @api.multi
    @api.depends('last_connected_time')
    def compute_last_connected_days(self):
        for rec in self:
            days = 40
            if rec.last_connected_time:
                last_connected_datetime = fields.Datetime.from_string(rec.last_connected_time)
                days = (datetime.now() - last_connected_datetime).days
            rec.last_connected_days = days


    @api.multi
    def download_from_log(self):
        for machine in self:
            logs=self.env['biometric.log'].sudo().search([])
            atts=[]
            for log in logs:
                atttime=datetime.strptime(log.name,DATETIME_FORMAT)
                print ('log time is',atttime)
                atts.append([log.employee_id.att_user_id,False,atttime])
            print('the total attts is',atts)
            self.action_create_atts(atts)

            
    def create_attendance_from_logs(self, current_att, current_att_str, employee, manual_id = None, machine_id= None):
        previous_attendance = self.env['hr.attendance'].search(
            ['&', ('employee_id', '=', employee.id), '|', ('check_in', '<', current_att_str),
             ('check_out', '<', current_att_str)], limit=1,
            order='check_in desc')
        previous_attendance_check = previous_attendance and fields.Datetime.from_string(
            previous_attendance.check_in)
        previous_attendance_date = previous_attendance and previous_attendance_check.date()
        delta_att = 0
        delta_att = previous_attendance and (current_att - previous_attendance_check).seconds or 0
        current_att_date = current_att.date()

        attendance_limit = datetime.combine(current_att_date, datetime.min.time()).replace(hour=3)
        machine = True if machine_id else False
        if delta_att > (23 * 60 * 60) and previous_attendance and not previous_attendance.check_out:
            p_check_out = datetime.strftime(previous_attendance_check + timedelta(seconds=1), DATETIME_FORMAT)
            previous_attendance.with_context(machine=machine).write(
                {'check_out': p_check_out, 'state': 'fix', 'check_out_machine_id': machine_id})
            self.env['hr.attendance'].with_context(machine=machine).create({
                'check_in': current_att_str,
                'employee_id': employee.id,
                'state': 'right',
                'check_in_machine_id': machine_id,
                'manual_in_id': manual_id,
            })

        elif previous_attendance and previous_attendance_date != current_att_date and not previous_attendance.check_out and current_att > attendance_limit:
            p_check_out = datetime.strftime(previous_attendance_check + timedelta(seconds=1), DATETIME_FORMAT)
            previous_attendance.with_context(machine=machine).write(
                {'check_out': p_check_out, 'state': 'fix', 'check_out_machine_id': machine_id})
            self.env['hr.attendance'].with_context(machine=machine).create({
                'check_in': current_att_str,
                'employee_id': employee.id,
                'state': 'right',
                'check_in_machine_id': machine_id,
                'manual_in_id': manual_id,
            })

        elif previous_attendance and not previous_attendance.check_out:
            previous_attendance.with_context(machine=machine).write(
                {'check_out': current_att_str, 'state': 'right', 'check_out_machine_id': machine_id,'manual_out_id': manual_id})

        elif previous_attendance.check_out or not previous_attendance:
            self.env['hr.attendance'].with_context(machine=machine).create({
                'check_in': current_att_str,
                'employee_id': employee.id,
                'state': 'right',
                'check_in_machine_id': machine_id,
                'manual_in_id': manual_id,
            })


    def correct_intersected_attendances(self,attendances, employee , intersected_attendances):
        print('employee ',employee.id)
        print('attendannces ', attendances)
        print('intersected attendances ', intersected_attendances)
        attends = []
        # min_attend_str = datetime.strftime(attendances[0], DATETIME_FORMAT)
        # start_time = min(intersected_attendances[0].check_in , min_attend_str)
        start_time = min(intersected_attendances[0].check_in , attendances[0])
        intersected_attendances.sudo().unlink()
        attendance_obj = self.env['hr.attendance']
        machine_logs = self.env['biometric.log'].sudo().search([
            ('employee_id','=',employee.id),
            ('name','>=',start_time),
        ])

        manual_logs = self.env['manual.attendance'].search([
            ('employee_id','=',employee.id),
            ('attendance_time','>=',start_time),
        ])

        for mac_log in machine_logs:
            attends.append(
                (mac_log.name,'machine',mac_log.machine.id)
            )

        for man_log in manual_logs:
            attends.append(
                (man_log.attendance_time,'manual',man_log.id)
            )

        attends.sort(key=lambda tup: tup[0])

        vals = {
            'employee_id': employee.id,
            'check_in': attends[0][0],
        }

        machine = False
        if attends[0][1] == 'machine':
            vals['check_in_machine_id'] = attends[0][2]
            machine = True
        # if attends[0][1] == 'manual':
        #     vals['check_in_machine_id'] = attends[0][2]

        first_attendance = attendance_obj.with_context(machine=machine).create(vals)
        last_attend = fields.Datetime.from_string(attends[0][0])
        for attend in attends[1:]:
            current_att_str = attend[0]
            current_att = fields.Datetime.from_string(current_att_str)            
            if last_attend and (current_att - last_attend) <= timedelta(minutes=1):
                last_attend = current_att
                continue

            else:
                last_attend = current_att
                if attend[1] == 'machine':
                    machine_id = attend[2]
                    self.create_attendance_from_logs(current_att,current_att_str,employee, machine_id = machine_id)
                
                elif attend[1] == 'manual':
                    manual_id = attend[2]
                    self.create_attendance_from_logs( current_att, current_att_str, employee ,manual_id = manual_id)

    # function to download attendance
    @api.multi
    def download_attendance(self):
        employee_obj = self.env['hr.employee']
        # machine_logs = {}
        # machine_attendances = set([])
        for machine in self:
            machine_ip = machine.ip_address
            port = machine.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=True)
            record_vals = {'name': datetime.now(),
                           'machine': machine.id}
            try:
                conn = zk.connect()
                # conn.enable_device()
                attendance = conn.get_attendance()
                # conn.enable_device()
                conn.disconnect()

            except Exception as e:
                _logger.info("++++++++++++Exception++++++++++++++++++++++", e)
                record_vals['state'] = 'failed'
                record_vals['note'] = 'Failed Connection and the error is(%s)' % e
                new_record = self.env['biometric.record'].sudo().create(record_vals)
                continue

            if attendance:
                try:
                    print('attendances is', attendance)
                    print('number of att', len(attendance))
                    # machine_logs[machine.id] = attendance
                    # machine_attendances |= set(attendance)
                    machine.action_create_log(attendance,machine.id)
                    machine.action_create_atts(attendance)
                    # zk.disconnect()
                    record_vals['state'] = 'success'
                    record_vals['note'] = 'successful connection and attendance records have been updated'
                    new_record = self.env['biometric.record'].sudo().create(record_vals)
                    # in case of successful attendance fetch
                    machine.write({'last_connected_time': str(datetime.now())})
                except Exception as e:
                    _logger.info("++++++++++++Exception++++++++++++++++++++++", e)
                    # zk.enable_device()
                    # zk.disconnect()
                    record_vals['state']='failed'
                    record_vals['note'] = 'Successful Connection But there is error while writing attendance records and the error is(%s)'%e
                    new_record = self.env['biometric.record'].sudo().create(record_vals)

            else:
                # zk.enable_device()
                # zk.disconnect()
                record_vals['state'] = 'success'
                record_vals['note'] = 'successful connection but there is no attendance records'
                new_record = self.env['biometric.record'].sudo().create(record_vals)
                # raise UserError(_('Unable to get the attendance log, please try again later.'))


    @api.multi
    def action_create_atts(self, atts):
        print('iam in create atts',atts)
        attend_machines = self.search([])
        last_connected = attend_machines.mapped('last_connected_time')
        min_last_connected = None
        default_connected = datetime.now() + timedelta(days=-40)

        # for l in last_connected:
        #     machine_last_date = l and fields.Datetime.from_string(l)
        #     if not l:
        #         min_last_connected = default_connected
        #         break
        #     elif l and not min_last_connected:
        #         min_last_connected = fields.Datetime.from_string(l)
        #     elif l and min_last_connected and machine_last_date < min_last_connected:
        #         min_last_connected = machine_last_date

        ## if min_last_connected > default_connected:
        ##     min_last_connected = min_last_connected + timedelta(days=-1)
        ##     min_last_connected = min_last_connected.replace(hour=0, minute=0, second=0)
        min_last_connected = default_connected
        min_last_connected = min_last_connected - timedelta(days=(min_last_connected.weekday() + 2) % 7)
        min_last_connected = min_last_connected.replace(hour=0, minute=0, second=0)
        print('min_last_connected ', min_last_connected)

        def convert_date_to_utc(date, tz):
            local = pytz.timezone(tz)
            date = local.localize(date, is_dst=None)
            date = date.astimezone(pytz.utc)
            date.strftime('%Y-%m-%d: %H:%M:%S')
            return date.replace(tzinfo=None)

        def convert_date_to_local(date, tz):
            local = pytz.timezone(tz)
            date = date.replace(tzinfo=pytz.utc)
            date = date.astimezone(local)
            date.strftime('%Y-%m-%d: %H:%M:%S')
            return date.replace(tzinfo=None)

        if atts is None:
            data = []
        for res in self:
            machine_id = res.id
            employee_obj = self.env['hr.employee']
            tz_info = res.timezone
            att_users = []
            users_atts = {}
            user_last_atts = {}
            for i,att in enumerate(atts):
                att_dict = vars(att)
                user_no = att_dict["user_id"]
                att_time = att_dict["timestamp"]
                if user_no not in att_users:
                    users_atts[user_no] = []
                    att_users.append(user_no)
                employee = employee_obj.search([('att_user_id', '=', user_no)], limit=1)
                if not employee:
                    continue

                if att_time >= min_last_connected:
                    att_time_utc = convert_date_to_utc(att_time, tz_info)
                    users_atts[user_no].append(att_time_utc)

            print('att_users is',att_users)
            print('users_atts is',users_atts)
            for user, atts in users_atts.items():
                print('user is', user)
                print('atts is', atts)

                employee = employee_obj.search([('att_user_id', '=', user)])
                attendances = sorted(atts)

                for attend in attendances[:]:

                    if user in user_last_atts and (attend - user_last_atts[user]) <= timedelta(minutes=1):
                        print('regected:', user, 'time ', attend, 'last attend ', user_last_atts[user])
                        user_last_atts[user] = attend
                        attendances.remove(attend)
                        continue

                    user_last_atts[user] = attend
                    str_att_time_utc = datetime.strftime(attend,DATETIME_FORMAT)
                    emp_prev_att = self.env['hr.attendance'].search(
                        [('employee_id.id', '=', employee.id), '|', ('check_in', '=', str_att_time_utc),
                         ('check_out', '=', str_att_time_utc)],
                        order="check_in")
                    if emp_prev_att:
                        attendances.remove(attend)
                        continue
                        # print('there is old atts i will not add them')

                if attendances:
                    count = len(attendances)
                else:
                    continue

                i = 0
                while i < count:
                    current_att = attendances[i]
                    current_att_str = datetime.strftime( current_att, DATETIME_FORMAT)
                    intersected_attendances = self.env['hr.attendance'].search(['&',('employee_id','=',employee.id),'|', ('check_in', '>', current_att_str), ('check_out', '>', current_att_str)],order='check_in')
                    if intersected_attendances:
                        print('current_att_str',current_att_str)
                        res.correct_intersected_attendances(attendances[i:], employee,intersected_attendances)
                        break
                    else:
                        self.create_attendance_from_logs(current_att, current_att_str, employee, machine_id = machine_id)
                        i += 1
                

    @api.multi
    def action_create_log(self, atts,machine_id):
        def convert_date_to_utc(date, tz):
            local = pytz.timezone(tz)
            date = local.localize(date, is_dst=None)
            date = date.astimezone(pytz.utc)
            date.strftime('%Y-%m-%d: %H:%M:%S')
            return date.replace(tzinfo=None)
        if atts is None:
            return
            data = []
        for res in self:
            employee_obj = self.env['hr.employee']
            log_obj = self.env['biometric.log']
            tz_info = res.timezone
            for i, att in enumerate(atts):
                att_dict = vars(att)
                user_no = att_dict["user_id"]
                employee = employee_obj.search([('att_user_id', '=', user_no)], limit=1)
                if not employee:
                    continue
                att_time = att_dict["timestamp"]
                str_att_time_utc = datetime.strftime(convert_date_to_utc(att_time, tz_info),
                                                     DATETIME_FORMAT)
                old_log = log_obj.sudo().search([
                    ('employee_id','=', employee.id),
                    ('name','=', str_att_time_utc),
                    ('machine','=', machine_id),
                ])
                if not old_log:
                    new_log = log_obj.sudo().create({
                        'employee_id':employee.id,
                        'name':str_att_time_utc,
                        'machine': machine_id,
                    })


    @api.multi
    def clear_attendance(self):
        for machine in self:
            machine_ip = machine.ip_address
            port = machine.port
            # print machine_ip,port
            try:
                zk = ZK(machine_ip, port=int(port),timeout=5)
                conn = zk.connect()

                conn.enable_device()
                conn.clear_attendance()
                conn.enable_device()
                conn.disconnect()
            except Exception as e:
                raise ValidationError(('Warning !'), ("Machine with is not connected"))

        # machine_ip = self.name
        # port = self.port
        # zk = zklib.ZKLib(machine_ip, int(port))
        #