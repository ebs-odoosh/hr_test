import itertools
from lxml import etree
import time
import pytz
import math
import datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.float_utils import float_compare, float_round
import babel
from operator import itemgetter

import logging

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


def float_to_time(float_type):
    str_off_time = str(float_type)
    official_hour = str_off_time.split('.')[0]
    official_minute = (
        "%2d" % int(
            str(float("0." + str_off_time.split('.')[1]) * 60).split('.')[
                0])).replace(
        ' ', '0')
    str_off_time = official_hour + ":" + official_minute
    str_off_time = datetime.strptime(str_off_time, "%H:%M").time()
    return str_off_time


def _get_float_from_time(time):
    time_type = datetime.strftime(time, "%H:%M")
    signOnP = [int(n) for n in time_type.split(":")]
    signOnH = signOnP[0] + signOnP[1] / 60.0
    return signOnH


def interval_clean(intervals):
    intervals = sorted(intervals, key=itemgetter(0))  # sort on first datetime
    cleaned = []
    working_interval = None
    while intervals:
        current_interval = intervals.pop(0)
        if not working_interval:  # init
            working_interval = [current_interval[0], current_interval[1]]
        elif working_interval[1] < current_interval[0]:  # interval is disjoint
            cleaned.append(tuple(working_interval))
            working_interval = [current_interval[0], current_interval[1]]
        elif working_interval[1] < current_interval[
            1]:  # union of greater intervals
            working_interval[1] = current_interval[1]
    if working_interval:  # handle void lists
        cleaned.append(tuple(working_interval))
    return cleaned


def interval_without_leaves(interval, leave_intervals):
    if not interval:
        return interval
    if leave_intervals is None:
        leave_intervals = []
    intervals = []
    leave_intervals = interval_clean(leave_intervals)
    current_interval = [interval[0], interval[1]]
    for leave in leave_intervals:
        if leave[1] <= current_interval[0]:
            continue
        if leave[0] >= current_interval[1]:
            break
        if current_interval[0] < leave[0] < current_interval[1]:
            current_interval[1] = leave[0]
            intervals.append((current_interval[0], current_interval[1]))
            current_interval = [leave[1], interval[1]]
        if current_interval[0] <= leave[1]:
            current_interval[0] = leave[1]
    if current_interval and current_interval[0] < interval[
        1]:  # remove intervals moved outside base interval due to leaves
        intervals.append((current_interval[0], current_interval[1]))
    return intervals


def get_overtime(policy):
    res = {}
    if policy:
        overtime_ids = policy.overtime_rule_ids
        wd_ot_id = policy.overtime_rule_ids.search(
            [('type', '=', 'workday'), ('id', 'in', overtime_ids.ids)],
            order='id', limit=1)
        we_ot_id = policy.overtime_rule_ids.search(
            [('type', '=', 'weekend'), ('id', 'in', overtime_ids.ids)],
            order='id', limit=1)
        ph_ot_id = policy.overtime_rule_ids.search(
            [('type', '=', 'ph'), ('id', 'in', overtime_ids.ids)], order='id',
            limit=1)
        if wd_ot_id:
            res['wd_rate'] = wd_ot_id.rate
            res['wd_after'] = wd_ot_id.active_after
        else:
            res['wd_rate'] = 1
            res['wd_after'] = 0
        if we_ot_id:
            res['we_rate'] = we_ot_id.rate
            res['we_after'] = we_ot_id.active_after
        else:
            res['we_rate'] = 1
            res['we_after'] = 0

        if ph_ot_id:
            res['ph_rate'] = ph_ot_id.rate
            res['ph_after'] = ph_ot_id.active_after
        else:
            res['ph_rate'] = 1
            res['ph_after'] = 0
    else:
        res['wd_rate'] = res['wd_rate'] = res['ph_rate'] = 1
        res['wd_after'] = res['we_after'] = res['ph_after'] = 0
    return res


def get_late(policy, period, cnt):
        res = period
        flag = False
        no=1
        cnt_flag=False
        factor=1
        if period<=0:
            return 0,cnt
        if policy:
            if policy.late_rule_id:
                time_ids = policy.late_rule_id.line_ids.sorted(key=lambda r: r.time, reverse=True)
                for line in time_ids:
                    if period >= line.time:
                        for counter in cnt:
                            if counter[0]==line.time:
                                cnt_flag=True
                                no = counter[1]
                                counter[1]+=1
                                break
                        if no >= 5 and line.fifth >= 0:
                            factor = line.fifth
                        elif no >=4 and line.fourth >= 0 :
                            factor = line.fourth
                        elif no >= 3 and line.third >= 0 :
                            factor = line.third
                        elif no >= 2 and line.second >= 0 :
                            factor = line.second
                        elif no >= 1 and line.first>= 0:
                            factor = line.first
                        elif no == 0 :
                            factor = 0
                        if not cnt_flag:
                            cnt.append([line.time,2])
                        flag = True
                        if line.type == 'rate':
                            res = line.rate * period *factor
                        elif line.type == 'fix':
                            res = line.amount*factor

                        break

                if not flag:
                    res = 0
        return res,cnt


def get_diff(policy, period, diff_cnt):
    res = period
    flag = False
    no = 1
    cnt_flag = False
    factor = 1
    if period <= 0:
        return 0, diff_cnt
    if policy:
        if policy.diff_rule_id:
            time_ids = policy.diff_rule_id.line_ids.sorted(key=lambda r: r.time, reverse=True)
            for line in time_ids:
                if period >= line.time:
                    for counter in diff_cnt:
                        if counter[0] == line.time:
                            cnt_flag = True
                            no = counter[1]
                            counter[1] += 1
                            break
                    if no >= 5:
                        factor = line.fifth
                    elif no >= 4:
                        factor = line.fourth
                    elif no >= 3:
                        factor = line.third
                    elif no >= 2:
                        factor = line.second
                    elif no >= 1:
                        factor = line.first
                    elif no >= 0:
                        factor = 1
                    if not cnt_flag:
                        diff_cnt.append([line.time, 2])
                    flag = True
                    if line.type == 'rate':
                        res = line.rate * period * factor
                    elif line.type == 'fix':
                        res = line.amount * factor
                    break
            if not flag:
                res = 0
        return res, diff_cnt


def get_absence(policy, period, cnt):
    res = period
    flag = False
    if policy:
        if policy.absence_rule_id:
            abs_ids = policy.absence_rule_id.line_ids.sorted(key=lambda r: r.counter, reverse=True)
            for ln in abs_ids:
                if cnt >= int(ln.counter):
                    res = ln.rate * period
                    flag = True
                    break
            if not flag:
                res = 0
    return res


class hr_public_holiday(models.Model):
    _name = "hr.public.holiday"
    _description = "hr.public.holiday"

    name = fields.Char(string="Reason")
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Not Active')], default='inactive', track_visibility='onchange',
        string='Status', required=True, index=True, )
    note = fields.Text("Notes")


class attendance_sheet(models.Model):
    _name = 'attendance.sheet'

    name = fields.Char("name",translate=True)

    @api.multi
    def action_attsheet_confirm(self):
        self.write({'state': 'confirm'})
        for line in self.att_sheet_line_ids:
            line.write({'state': 'confirm'})
        return True

    @api.multi
    def action_attsheet_approve(self):
        self.calculate_att_data()
        self.write({'state': 'done'})
        for line in self.att_sheet_line_ids:
            line.write({'state': 'done'})
        return True

    @api.multi
    def action_attsheet_draft(self):
        self.write({'state': 'draft'})
        for line in self.att_sheet_line_ids:
            line.write({'state': 'draft'})
        return True

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    date_from = fields.Date(string="From", required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string="To", required=True,
                          default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    att_sheet_line_ids = fields.One2many(comodel_name='attendance.sheet.line', string='Attendances',readonly=True,
                                         inverse_name='att_sheet_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    no_overtime = fields.Integer(compute="calculate_att_data", string="No of overtimes", readonly=True, store=True)
    tot_overtime = fields.Float(compute="calculate_att_data", string="Total Over Time", readonly=True, store=True)
    tot_difftime = fields.Float(compute="calculate_att_data", string="Total Diff time Hours", readonly=True, store=True)
    no_difftime = fields.Integer(compute="calculate_att_data", string="No of Diff Times", readonly=True, store=True)
    tot_late = fields.Float(compute="calculate_att_data", string="Total Late In", readonly=True, store=True)
    no_late = fields.Integer(compute="calculate_att_data", string="No of Lates", readonly=True, store=True)
    no_absence = fields.Integer(compute="calculate_att_data", string="No of Absence Days", readonly=True, store=True)
    tot_absence = fields.Float(compute="calculate_att_data", string="Total absence Hours", readonly=True, store=True)
    tot_wh = fields.Float(compute="calculate_att_data", string="Total Working Hours", readonly=True, store=True)
    no_wd = fields.Float(compute="calculate_att_data", string="No of worked days", readonly=True, store=True)

    # New to get weekends and public holidays
    tot_weekend_holidays = fields.Float(compute="calculate_att_data", string="Total Weekends And Holidays",
                                        readonly=True, store=True)
    no_weekend_holidays = fields.Float(compute="calculate_att_data", string="No of weekends and Holidays",
                                       readonly=True, store=True)

    att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy', string="Attendance Policy ", required=True)
    payslip_id=fields.Many2one(comodel_name='hr.payslip',string='PaySlip',copy=False)

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        # ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        locale = self.env.context.get('lang', 'en_US')
        if locale == "ar_SY":
            locale = "ar"
        self.name = _('Attendance Sheet of %s for %s') % (employee.name,
                                                          tools.ustr(
                                                              babel.dates.format_date(date=date_from, format='MMMM-y',
                                                                                      locale=locale)))
        self.company_id = employee.company_id

        contract_ids = self.env['hr.payslip'].get_contract(employee, date_from, date_to)
        if not contract_ids:
            return
        self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.att_policy_id:
            raise ValidationError(_("Employee %s does not have attendance policy"%employee.name))
            return
        self.att_policy_id = self.contract_id.att_policy_id

    @api.multi
    def calculate_att_data(self):
        overtime = 0
        no_overtime = 0
        late = 0
        no_late = 0
        diff = 0
        no_diff = 0
        tot_wh=0
        no_wd=0
        absence_hours = 0
        no_absence = 0

        # New change
        no_we_ph = 0
        weekend_holidays = 0
        # end change

        for att_sheet in self:
            for line in att_sheet.att_sheet_line_ids:
                # New Change to separate between overtime and weekends
                if line.overtime > 0 and not line.status:
                    overtime += line.overtime
                    no_overtime = no_overtime + 1
                if line.overtime > 0 and line.status in ['weekend','ph']:
                    weekend_holidays += line.overtime
                    no_we_ph = no_we_ph + 1
                #  end of New change

                if line.diff_time > 0:
                    if line.status == "ab":
                        no_absence += 1
                        absence_hours += line.diff_time
                    else:
                        diff += line.diff_time
                        no_diff += 1
                if line.late_in > 0:
                    late += line.late_in
                    no_late += 1
                if line.worked_hours>0:
                    tot_wh+=line.worked_hours
                    no_wd+=1

            # New Change to prevent error while upgrade module
            att_sheet.tot_overtime = overtime
            att_sheet.no_overtime = no_overtime
            att_sheet.tot_difftime = diff
            att_sheet.no_difftime = no_diff
            att_sheet.no_absence = no_absence
            att_sheet.tot_absence = absence_hours
            att_sheet.tot_late = late
            att_sheet.no_late = no_late
            att_sheet.tot_wh = tot_wh
            att_sheet.no_wd = no_wd
            att_sheet.no_weekend_holidays = no_we_ph
            att_sheet.tot_weekend_holidays = weekend_holidays


            # values = {
            #     'tot_overtime': overtime,
            #     'no_overtime': no_overtime,
            #     'tot_difftime': diff,
            #     'no_difftime': no_diff,
            #     'no_absence': no_absence,
            #     'tot_absence': absence_hours,
            #     'tot_late': late,
            #     'no_late': no_late,
            #     'tot_wh':tot_wh,
            #     'no_wd':no_wd,
            #     'no_weekend_holidays':no_we_ph,
            #     'tot_weekend_holidays':weekend_holidays,
            #
            # }
            # att_sheet.write(values)

    @api.model
    def _get_leave(self, emp, date):
        res = {}
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate'),
            ('type', '=', 'remove')]).ids

        if leave_ids:
            for leave in leave_obj.browse(leave_ids):
                leave_date_from = datetime.strptime(leave.date_from,
                                                    "%Y-%m-%d %H:%M:%S").date()
                leave_date_to = datetime.strptime(leave.date_to,
                                                  "%Y-%m-%d %H:%M:%S").date()
                if leave_date_from <= date and leave_date_to >= date:
                    res['leave_name'] = leave.name
                    res['leave_type'] = leave.holiday_status_id.name
        print("leaves", res)
        return res

    @api.multi
    def _get_emp_leave_intervals(self, emp, start_datetime=None, end_datetime=None):
        leaves = []
        tz_info = fields.Datetime.context_timestamp(self, start_datetime).tzinfo
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate'), ])
        for leave in leave_ids:
            date_from = fields.Datetime.from_string(leave.date_from)
            date_to = fields.Datetime.from_string(leave.date_to)
            if end_datetime and date_from > end_datetime:
                continue
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append((date_from, date_to))
        return leaves

    def get_public_holiday(self, date):
        public_holiday = self.env['hr.public.holiday'].search(
            [('date_from', '<=', date), ('date_to', '>=', date),
             ('state', '=', 'active')])
        return public_holiday

    def get_work_intervals(self, day_start, day_end):
        calendar_id = self.employee_id.contract_id.resource_calendar_id
        tz_info = fields.Datetime.context_timestamp(self, day_start).tzinfo
        working_intervals = []
        for att in calendar_id._get_day_attendances(day_start.date(),
                                                    day_start.replace(hour=0,
                                                                      minute=0,
                                                                      second=0).time(),
                                                    day_end.time()):
            dt_f = day_start.replace(hour=0, minute=0, second=0) + timedelta(
                seconds=(att.hour_from * 3600))
            if dt_f < day_start:
                dt_f = day_start
            dt_t = day_start.replace(hour=0, minute=0, second=0) + timedelta(
                seconds=(att.hour_to * 3600))
            if dt_t > day_end:
                dt_t = day_end
            working_interval = (dt_f, dt_t)
            # adapt tz
            working_interval_tz = (
                dt_f.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(
                    tzinfo=None),
                dt_t.replace(tzinfo=tz_info).astimezone(pytz.UTC).replace(
                    tzinfo=None))
            working_intervals.append(working_interval_tz)
        clean_work_intervals = interval_clean(working_intervals)
        return working_intervals

    def get_attendance_intervals(self, emp, day_start, day_end):
        tz_info = fields.Datetime.context_timestamp(self, day_start).tzinfo
        day_st_utc = day_start.replace(tzinfo=tz_info).astimezone(
            pytz.utc).replace(tzinfo=None)
        str_day_st_utc = datetime.strftime(day_st_utc, DATETIME_FORMAT)
        day_end_utc = day_end.replace(tzinfo=tz_info).astimezone(
            pytz.utc).replace(tzinfo=None)
        str_day_end_utc = datetime.strftime(day_end_utc, DATETIME_FORMAT)
        res = []
        attendances = self.env['hr.attendance'].search(
            [('employee_id.id', '=', emp.id),
             ('check_in', '>=', str_day_st_utc),
             ('check_in', '<=', str_day_end_utc),
             ('check_out', '!=', False)], order="check_in")

        for att in attendances:
            check_in = datetime.strptime(str(att.check_in), DATETIME_FORMAT)
            check_out = datetime.strptime(str(att.check_out), DATETIME_FORMAT)
            res.append((check_in, check_out))
        return res

    @api.multi
    def get_attendances(self):
        for att_sheet in self:
            att_sheet.att_sheet_line_ids.unlink()
            att_line = self.env["attendance.sheet.line"]
            from_date = datetime.strptime(str(att_sheet.date_from), "%Y-%m-%d")
            to_date = datetime.strptime(str(att_sheet.date_to), "%Y-%m-%d")
            emp = att_sheet.employee_id
            if not self.env.user.tz:
                raise exceptions.Warning("Please add time zone for %s" % emp.name)
            else:
                tz = pytz.timezone(self.env.user.tz)

            if not(emp.contract_id and emp.contract_id.state == 'open'):
                raise ValidationError(_(
                    'There is no running contract for %s ' % emp.name))

            if att_sheet.att_policy_id:
                policy_id = att_sheet.att_policy_id
            else:
                raise ValidationError(_(
                    'Please add Attendance Policy to the %s `s contract ' % emp.name))
                return

            # New change to limit attendance sheet to the end of contract if contract expired
            if self.employee_id.contract_id and self.employee_id.contract_id.date_end:
                contract = self.employee_id.contract_id
                contract_end_date = datetime.strptime(str(contract.date_end), "%Y-%m-%d")
                to_date = min(to_date,contract_end_date)
            # end change


            # New change to limit attendance sheet to the start of contract if contract starts in the same month
            if self.employee_id.contract_id:
                contract = self.employee_id.contract_id
                contract_start_date = datetime.strptime(str(contract.date_start), "%Y-%m-%d")
                from_date = max(from_date,contract_start_date)
            # end change


            all_dates = [(from_date + timedelta(days=x)) for x in range((to_date - from_date).days + 1)]
            abs_cnt = 0
            late_cnt=[]
            diff_cnt=[]
            for day in all_dates:
                day_start = day
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
                data = {}
                day_str = str(day.weekday())
                date = day.strftime('%Y-%m-%d')
                late_in = timedelta(hours=00, minutes=00, seconds=00)
                overtime = timedelta(hours=00, minutes=00, seconds=00)
                diff_time = timedelta(hours=00, minutes=00, seconds=00)
                work_intervals = self.get_work_intervals(day_start=day_start, day_end=day_end)
                attendance_intervals = self.get_attendance_intervals(emp, day_start, day_end)
                leave_day_end = day_end

                if work_intervals:
                    leave_day_end = list(max(work_intervals))[1]
                leaves = self._get_emp_leave_intervals(emp, day_start, leave_day_end)

                public_holiday = self.get_public_holiday(date)
                reserved_intervals = []
                overtime_policy = get_overtime(policy_id)
                flexible = self.employee_id.contract_id.resource_calendar_id.flexible_hours
                if work_intervals:
                    if public_holiday:
                        if attendance_intervals:
                            for attendance_interval in attendance_intervals:
                                overtime = attendance_interval[1] - attendance_interval[0]
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['ph_after']:
                                    float_overtime = 0
                                else:
                                    # New change to round overtime hours to nearest half hours
                                    # for example 14 rounded to 0 , 15 rounded to 0 , 16 rounded to 30 , 35 rounded to 30 , 45 rounded to 30 ,48 rounded to 60 minutes
                                    float_overtime = (float_overtime*60.0 + 14.0)/30
                                    float_overtime = math.floor(float_overtime)
                                    float_overtime /= 2
                                    # End change

                                    float_overtime = float_overtime * overtime_policy['ph_rate']

                                ac_sign_in = pytz.utc.localize(attendance_interval[0]).astimezone(tz)
                                ac_sign_out = pytz.utc.localize(attendance_interval[1]).astimezone(tz)

                                worked_hours=attendance_interval[1] - attendance_interval[0]
                                float_worked_hours = worked_hours.total_seconds() / 3600

                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'ac_sign_in': _get_float_from_time(ac_sign_in),
                                    'ac_sign_out': _get_float_from_time(ac_sign_out),
                                    'worked_hours':float_worked_hours,
                                    'overtime': float_overtime,
                                    'att_sheet_id': self.id,
                                    'status': 'ph',
                                    'note': _("working on Public Holiday")
                                }
                                att_line.create(values)
                        else:
                            values = {
                                'date': date,
                                'day': day_str,
                                'att_sheet_id': self.id,
                                'status': 'ph',
                            }
                            att_line.create(values)

                    else:
                        for i, work_interval in enumerate(work_intervals):
                            att_work_intervals = []
                            diff_intervals = []
                            late_in_interval = []
                            out_work_intervals = []
                            policy_diff = 0
                            float_worked_hours = 0
                            for j, att_interval in enumerate(attendance_intervals):
                                if max(work_interval[0], att_interval[0]) < min(work_interval[1], att_interval[1]):
                                    att_work_intervals.append(att_interval)
                                else:
                                    out_work_intervals.append(att_interval)
                            if att_work_intervals:
                                for att in out_work_intervals:
                                    if work_interval[0] < att_interval[1]:
                                        att_work_intervals.append(att)
                            att_work_intervals.sort()
                            reserved_intervals += att_work_intervals
                            pl_sign_in = _get_float_from_time(pytz.utc.localize(work_interval[0]).astimezone(tz))
                            pl_sign_out = _get_float_from_time(pytz.utc.localize(work_interval[1]).astimezone(tz))
                            ac_sign_in = 0
                            ac_sign_out = 0
                            status = ""
                            note = ""
                            if att_work_intervals:
                                if flexible and att_work_intervals[0][0] > work_interval[0]:

                                    flexible_clean_intervals = (work_interval[0], work_interval[0] + timedelta(hours=flexible))
                                    if leaves:
                                        flexible_clean_intervals = interval_without_leaves(flexible_clean_intervals, leaves)

                                    if flexible_clean_intervals:
                                        diff_hours = \
                                            (att_work_intervals[0][0] - work_interval[0]).total_seconds() / 3600
                                        if diff_hours:
                                            work_interval = list(work_interval)
                                            if diff_hours > flexible:
                                                diff_hours = flexible
                                            work_interval[0] = work_interval[0] + timedelta(hours=diff_hours)
                                            work_interval[1] = work_interval[1] + timedelta(hours=diff_hours)
                                            work_interval = tuple(work_interval)
                                late_in_interval = (work_interval[0], att_work_intervals[0][0])
                                overtime_interval = (work_interval[1], att_work_intervals[-1][1])
                                if overtime_interval[1] < overtime_interval[0]:
                                    overtime = timedelta(hours=0, minutes=0, seconds=0)
                                    diff_intervals.append((overtime_interval[1], overtime_interval[0]))
                                else:
                                    overtime = overtime_interval[1] - overtime_interval[0]
                                ac_sign_in = \
                                    pytz.utc.localize(att_work_intervals[0][0]).astimezone(tz)
                                ac_sign_out = \
                                    pytz.utc.localize(att_work_intervals[-1][1]).astimezone(tz)
                                worked_hours = ac_sign_out - ac_sign_in
                                float_worked_hours = worked_hours.total_seconds() / 3600
                            else:
                                late_in_interval = []
                                diff_intervals.append((work_interval[0], work_interval[1]))
                                status = "ab"
                            if diff_intervals:
                                for diff_in in diff_intervals:
                                    if leaves:
                                        diff_clean_intervals = interval_without_leaves(diff_in, leaves)
                                        if diff_clean_intervals != diff_in:
                                           status = "leave"
                                        for diff_clean in diff_clean_intervals:
                                            diff_time += diff_clean[1] - diff_clean[0]

                                    else:
                                        diff_time += diff_in[1] - diff_in[0]
                            if late_in_interval:
                                if late_in_interval[1] <= late_in_interval[0]:
                                    late_in = timedelta(hours=0, minutes=0, seconds=0)
                                else:
                                    if leaves:
                                        late_clean_intervals = interval_without_leaves(late_in_interval, leaves)
                                        if late_in_interval != late_clean_intervals:
                                           status = "leave"
                                        for late_clean in late_clean_intervals:
                                            late_in += late_clean[1] - late_clean[0]
                                    else:
                                        late_in = late_in_interval[1] - late_in_interval[0]
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['wd_after']:
                                float_overtime = 0
                            else:
                                # New change to round overtime hours to nearest half hours
                                # for example 14 rounded to 0 , 15 rounded to 0 , 16 rounded to 30 , 35 rounded to 30 , 45 rounded to 30 ,48 rounded to 60 minutes
                                float_overtime = (float_overtime * 60.0 + 14.0) / 30
                                float_overtime = math.floor(float_overtime)
                                float_overtime /= 2
                                # End change
                                float_overtime = float_overtime * overtime_policy['wd_rate']

                            float_late = late_in.total_seconds() / 3600
                            policy_late,late_cnt = get_late(policy_id, float_late,late_cnt)


                            float_diff = diff_time.total_seconds() / 3600
                            if status == 'ab':
                                abs_cnt += 1
                                float_diff = get_absence(policy_id, float_diff, abs_cnt)
                            else:
                                float_diff, diff_cnt = get_diff(policy_id, float_diff, diff_cnt)
                            att_status = False
                            if policy_late:
                                att_status = 'late'
                                if float_overtime:
                                    att_status = 'over+late'
                                elif float_diff:
                                    att_status = 'diff+late'

                            elif float_diff:
                                att_status = 'diff'
                            elif overtime:
                                att_status = 'over'
                            values = {
                                'date': date,
                                'day': day_str,
                                'pl_sign_in': pl_sign_in,
                                'pl_sign_out': pl_sign_out,
                                'ac_sign_in': _get_float_from_time(ac_sign_in) if float_worked_hours
                                else ac_sign_in,
                                'ac_sign_out': _get_float_from_time(ac_sign_out)
                                    if float_worked_hours else ac_sign_out,
                                'late_in': policy_late,
                                'overtime': float_overtime,
                                'worked_hours': float_worked_hours,
                                'diff_time': float_diff,
                                'status': status,
                                'att_status': att_status,
                                'att_sheet_id': self.id

                            }
                            att_line.create(values)
                        out_work_intervals = [x for x in attendance_intervals if x not in reserved_intervals]
                        if out_work_intervals:
                            for att_out in out_work_intervals:
                                overtime = att_out[1] - att_out[0]
                                ac_sign_in = pytz.utc.localize(att_out[0]).astimezone(
                                    tz)
                                ac_sign_out = pytz.utc.localize(att_out[1]).astimezone(
                                    tz)
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['wd_after']:
                                    float_overtime = 0
                                else:
                                    # New change to round overtime hours to nearest half hours
                                    # for example 14 rounded to 0 , 15 rounded to 0 , 16 rounded to 30 , 35 rounded to 30 , 45 rounded to 30 ,48 rounded to 60 minutes
                                    float_overtime = (float_overtime*60.0 + 14.0)/30
                                    float_overtime = math.floor(float_overtime)
                                    float_overtime /= 2
                                    # End change
                                    float_overtime = float_overtime * overtime_policy['wd_rate']
                                worked_hours = ac_sign_out - ac_sign_in
                                float_worked_hours = worked_hours.total_seconds() / 3600
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'pl_sign_in': 0,
                                    'pl_sign_out': 0,
                                    'ac_sign_in': _get_float_from_time(ac_sign_in),
                                    'ac_sign_out': _get_float_from_time(ac_sign_out),
                                    'overtime': float_overtime,
                                    'worked_hours': float_worked_hours,
                                    'note': _("overtime out of work intervals"),
                                    'att_sheet_id': self.id

                                }
                                att_line.create(values)

                else:
                    if attendance_intervals:
                        for attendance_interval in attendance_intervals:
                            overtime = attendance_interval[1] - attendance_interval[0]
                            ac_sign_in = pytz.utc.localize(attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(attendance_interval[1]).astimezone(tz)
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['we_after']:
                                float_overtime = 0
                            else:
                                # New change to round overtime hours to nearest half hours
                                # for example 14 rounded to 0 , 15 rounded to 0 , 16 rounded to 30 , 35 rounded to 30 , 45 rounded to 30 ,48 rounded to 60 minutes
                                float_overtime = (float_overtime * 60.0 + 14.0) / 30
                                float_overtime = math.floor(float_overtime)
                                float_overtime /= 2
                                # End change
                                float_overtime = float_overtime * overtime_policy['we_rate']
                            worked_hours = ac_sign_out - ac_sign_in
                            #########
                            float_worked_hours = worked_hours.total_seconds() / 3600
                            values = {
                                'date': date,
                                'day': day_str,
                                'ac_sign_in': _get_float_from_time(ac_sign_in),
                                'ac_sign_out': _get_float_from_time(ac_sign_out),
                                'overtime': float_overtime,
                                'worked_hours': float_worked_hours,
                                'att_sheet_id': self.id,
                                'status': 'weekend',
                                'note': _("working in weekend")

                            }
                            att_line.create(values)
                    else:
                        values = {
                            'date': date,
                            'day': day_str,
                            'att_sheet_id': self.id,
                            'status': 'weekend',
                            'note': ""

                        }
                        att_line.create(values)

    @api.multi
    def create_payslip(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                new_payslip=att_sheet.payslip_id
                continue

            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get('worked_days_line_ids')
            worktime = [{
                'name': "Worked Hours",
                'code': 'WH',
                'contract_id': contract_id,
                'sequence': 20,
                'number_of_days': att_sheet.no_wd,
                'number_of_hours': att_sheet.tot_wh,
            }]
            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            # New change
            weekend_holiday = [{
                'name': "Week ends and Holidays",
                'code': 'WEHD',
                'contract_id': contract_id,
                'sequence': 49,
                'number_of_days': att_sheet.no_weekend_holidays,
                'number_of_hours': att_sheet.tot_weekend_holidays,
            }]
            # End New Change
            worked_days_line_ids += overtime + late + absence + difftime + worktime + weekend_holiday
            # worked_days_line_ids += overtime + late + absence

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id=new_payslip
            payslips += new_payslip
        # payslips.compute_sheet()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': new_payslip.id,
            'views': [(False, 'form')],
        }

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("Can't delete confirmed sheet"))


class attendance_sheet_line(models.Model):
    _name = 'attendance.sheet.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft',readonly=True,)
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
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet', string='Attendance Sheet',readonly=True)
    pl_sign_in = fields.Float("Planned sign in",readonly=True)
    pl_sign_out = fields.Float("Planned sign out",readonly=True)
    worked_hours = fields.Float("Worked Hours",readonly=True)
    ac_sign_in = fields.Float("Actual sign in",readonly=True)
    ac_sign_out = fields.Float("Actual sign out",readonly=True)
    overtime = fields.Float("Overtime",readonly=True)
    late_in = fields.Float("Late In",readonly=True)
    diff_time = fields.Float("Diff Time", help="Diffrence between the working time and attendance time(s) ",readonly=True)
    note = fields.Text("Note",readonly=True)
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'), ('weekend', 'Week End'), ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'), ],
                              required=False,readonly=True)
    att_status = fields.Selection(string="Att Status",
                                  selection=[('late', 'Late In'), ('diff', 'Early Leave'),
                                             ('over', 'Overtime'),
                                             ('over+late', 'Late In, Overtime'),
                                             ('diff+late', 'Late In, Early Leave'), ],
                                  required=False, readonly=True)
    note = fields.Text("Note",readonly=True,translate=True)
