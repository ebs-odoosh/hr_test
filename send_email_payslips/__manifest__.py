# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Send Email Payslips",
    'version': '12.0.1.0.0',
    'summary': """Send Payslip by Email""",
    'description': """This module allow send payslip by mail""",
    'author': "El-sayed Muhammed Iraky & Islam Abdelmaaboud",
    'company': "ITSS",
    'website': "http://www.itss-sys.com",
    'category': 'HR',
    'depends': ['base', 'hr', 'hr_payroll'],
    'data': [
        'views/send_payslip.xml',
        'views/payslip_mail_template.xml',
    ],
    'images': [''],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
