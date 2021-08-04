

from odoo import models, fields, api




class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def get_work_factor(self,date_from,date_to):

        salary_start = max(self.date_start,date_from)
        salary_end = min(self.date_end,date_to) if self.date_end else date_to

        # This the case of normal payslip (month does not contain join date or contract end )
        if salary_start == date_from and salary_end == date_to:
            return 1

        salary_start_datetime = fields.Datetime.from_string(salary_start)
        salary_end_datetime = fields.Datetime.from_string(salary_end)

        # The case of month contain contract end i.e. employee termination or resignation
        if salary_start == date_from:
            month_end = fields.Datetime.from_string(date_to)
            month_days_count = (month_end - salary_start_datetime).days + 1
            num_work_days = (salary_end_datetime - salary_start_datetime).days + 1

            return (1.0*num_work_days)/(1.0*month_days_count)

        # The case of month contain join date i.e. first month for an employee (new employee)
        if salary_end == date_to:
            month_start = fields.Datetime.from_string(date_from)
            month_days_count = (salary_end_datetime - month_start).days + 1
            num_work_days = (salary_end_datetime - salary_start_datetime).days + 1

            return (1.0 * num_work_days) / (1.0 * month_days_count)

        # The case of employee that join and resigned on the same month
        else:
            month_start = fields.Datetime.from_string(date_from)
            month_end = fields.Datetime.from_string(date_to)
            month_days_count = (month_end - month_start).days + 1
            num_work_days = (salary_end_datetime - salary_start_datetime).days + 1

            return (1.0 * num_work_days) / (1.0 * month_days_count)

