# -*- coding: utf-8 -*-
""" init object """

import xlwt
import base64
from io import BytesIO
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,UserError

import logging
LOGGER = logging.getLogger(__name__)


class LeavesReport(models.TransientModel):
    _name = 'leaves.report'

    holiday_status_id = fields.Many2one(
        "hr.leave.type",
        string="Leave Type",
        domain=[('allocation_type', '=', 'fixed_allocation')],
    )
    department_id = fields.Many2many(
        comodel_name='hr.department',
        string='Departments',
    )
    category_ids = fields.Many2many(
        comodel_name='hr.employee.category',
        string='Tags'
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Employees",
    )

    leave_type_request_unit = fields.Selection(
        related='holiday_status_id.request_unit',
    )


    @api.onchange('category_ids','department_id',)
    def _onchange_employee_id(self):
        """Change employee domain with changing the department and
        the employees' categories """
        domain = []
        if self.department_id:
            domain.append(('department_id', 'in',
                           self.department_id.ids),
                          )
        if self.category_ids:
            domain.append(('category_ids', 'in',
                           self.category_ids.ids),
                          )

        return {'domain': {'employee_ids': domain}}

         # get allocation value
    def get_alloctin(self,employee,type):
        res = self.env['hr.leave.allocation'].search(
            [
                ('employee_id','=',employee),
      #          ('state', '=', 'validate'),
                ('holiday_status_id','=',type),
            ])
        total = 0.0
        for rec in res:
            total += rec.number_of_days_display
        return total
        # get leaves value

    def get_leaves(self, employee, type):
        res = self.env['hr.leave'].search(
            [
                ('employee_id', '=', employee),
 #               ('state', '=', 'validate'),
                ('holiday_status_id', '=', type),
            ])

        total = 0.0
        for rec in res:
            total += rec.number_of_days_display
        return total

    def get_report_data(self):
        lst_tags =  self.category_ids.ids
        lst_part =  self.department_id.ids
        leave_type_request_unit = self.leave_type_request_unit
        data = []
        for emp in self.employee_ids:
            alloct = self.get_alloctin(emp.id,self.holiday_status_id.id)
            leaves = self.get_leaves(emp.id,self.holiday_status_id.id)
            remining = alloct - leaves
            dt={
                'name':emp.name,
                'alloct':alloct,
                'remaining':remining,
                'leave_type_request_unit': leave_type_request_unit,
            }
            data.append(dt)
        return data

    # get tag field value
    def get_tags(self):
        names = ' '
        for line in  self.category_ids:
            names += ' - '+line.name
        return names


    # get department field value
    def get_depart(self):
        names = ' '
        for line in self.department_id:
            names += ' - ' + line.name
        return names


    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data = self.get_report_data()
        workbook = xlwt.Workbook()
        TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour tan, pattern_back_colour tan'
        )

        TABLE_HEADER_batch = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour light_green, pattern_back_colour light_green'
        )
        header_format = xlwt.easyxf(
            'font: bold 1, name Aharoni , color-index black,height 250;'
            'align: vertical center, horizontal center, wrap off;'
            'alignment: wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray25, pattern_back_colour gray25'
        )
        TABLE_HEADER_payslib = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour silver_ega, pattern_back_colour silver_ega'
        )
        TABLE_HEADER_Data = TABLE_HEADER
        TABLE_HEADER_Data.num_format_str = '#,##0.00_);(#,##0.00)'
        STYLE_LINE = xlwt.easyxf(
            'align: vertical center, horizontal center, wrap off;',
            'borders: left thin, right thin, top thin, bottom thin; '
            # 'num_format_str: General'
        )
        STYLE_Description_LINE = xlwt.easyxf(
            'align: vertical center, horizontal left, wrap 1;',
            'borders: left thin, right thin, top thin, bottom thin;'
        )

        TABLE_data = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour white, pattern_back_colour white'
        )
        TABLE_data.num_format_str = '#,##0.00'
        xlwt.add_palette_colour("gray11", 0x11)
        workbook.set_colour_RGB(0x11, 222, 222, 222)
        TABLE_data_tolal_line = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index white,height 200;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour blue_gray, pattern_back_colour blue_gray'
        )

        TABLE_data_tolal_line.num_format_str = '#,##0.00'
        TABLE_data_o = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray11, pattern_back_colour gray11'
        )
        STYLE_LINE_Data = STYLE_LINE
        STYLE_LINE_Data.num_format_str = '#,##0.00_);(#,##0.00)'

        # for branch in data:
        worksheet = workbook.add_sheet(_('Leaves Report'))
        lang = self.env.user.lang
        if lang == "ar_SY":
            worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 10
        worksheet.col(2).width = 256 * 10
        worksheet.col(3).width = 256 * 30
        worksheet.col(4).width = 256 * 30
        worksheet.col(5).width = 256 * 30
        worksheet.col(6).width = 256 * 30
        row = 2
        col = 3
        worksheet.write_merge(0, row, col, col + 3, _("Leaves Remaining Report"), header_format)
        row += 2
        col=3
        worksheet.write(row, col, _('Leave Type'), header_format)
        col += 1
        worksheet.write(row, col, str(self.holiday_status_id.name), TABLE_data)
        col = 3
        row +=1

        worksheet.write(row, col, _('Tag'), header_format)
        col += 1
        tags= self.get_tags()
        worksheet.write(row, col, str(tags), TABLE_data)
        col = 3
        row +=1

        worksheet.write(row, col, _('Department'), header_format)
        col += 1
        derart = self.get_depart()
        worksheet.write(row, col, str(derart), TABLE_data)

        row += 2
        col = 3

        worksheet.write(row, col, _('Name'), header_format)
        col += 1
        worksheet.write(row, col, _('Leaves Allocation'), header_format)
        col += 1
        worksheet.write(row, col, _('Remaining Leaves'), header_format)
        col += 1
        worksheet.write(row, col, _('Days/Hours'), header_format)
        col += 1


        for d in data:
            row += 1
            col = 3
            worksheet.write(row, col, d['name'], TABLE_data)
            col += 1
            worksheet.write(row, col, d['alloct'], TABLE_data)
            col += 1
            worksheet.write(row, col, d['remaining'], TABLE_data)
            col += 1
            worksheet.write(row, col, d['leave_type_request_unit'], TABLE_data)




        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('Report leaves.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'leaves.report'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'leaves.report',
                'res_id': self.id,
                'type': 'binary',
                'db_datas': base64.b64encode(output.getvalue()),
            })

            # Close the String Stream after saving it in the attachments
            output.close()
            url = '/web/content/%s/%s' % (attachment_obj.id, xls_file_path)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

        else:

            view_action = {
                'name': _(' Print leaves Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'leaves.report',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action

    def action_print(self):
        return self.action_print_excel_file()



