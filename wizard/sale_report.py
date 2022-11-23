# -*- coding: utf-8 -*-

import json
import io
from datetime import datetime
from xlsxwriter import workbook

from odoo.tools import date_utils
from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportAdvance(models.TransientModel):
    _name = "sale.order.salesperson"

    user_id = fields.Many2many('res.users', string="Salespersons")
    from_date = fields.Date(string="Start Date")
    to_date = fields.Date(string="End Date")
    type = fields.Selection([('user', 'Salespersons')], string='Report Print By', default='user', reqired=True)
    company_ids = fields.Many2many('res.company', string='Companies')
    today_date = fields.Date(default=fields.Date.today())

    def _get_data(self):
        sale = self.env['sale.order'].search([('state','!=','cancel')])
        sales_order_line = self.env['sale.order.line'].search([('order_id.state','!=','cancel')])

        if self.from_date and self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.date_order.date() <= self.to_date and x.company_id in self.company_ids,
                                      sale))
        elif not self.from_date and self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() <= self.to_date and x.company_id in self.company_ids,
                                      sale))
        elif self.from_date and not self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.company_id in self.company_ids,
                                      sale))
        elif self.from_date and self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date and x.date_order.date() <= self.to_date,
                                      sale))
        elif not self.from_date and not self.to_date and self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.company_id in self.company_ids,
                                      sale))
        elif not self.from_date and self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() <= self.to_date,
                                      sale))
        elif self.from_date and not self.to_date and not self.company_ids:
            sales_order = list(filter(lambda
                                          x: x.date_order.date() >= self.from_date,
                                      sale))
        else:
            sales_order = sale
        result = []
        users = []
        for rec in self.user_id:
            a = {
                'id': rec,
                'name': rec.name
            }
            users.append(a)

        if self.type == 'user':
            for rec in users:
                for so in sales_order:
                    if so.user_id == rec['id']:
                        for lines in so.order_line:
                            res = {
                                'sequence': so.name,
                                'date': so.date_order,
                                'product': lines.product_id.name,
                                'quantity': lines.product_uom_qty,
                                'price': lines.product_id.list_price,
                                'subtotal': lines.price_subtotal,
                                'user_id': so.user_id,
                            }
                            result.append(res)

        if self.from_date and self.to_date and not self.user_id:
            for so in sales_order:
                for lines in so.order_line:
                    res = {
                        'sequence': so.name,
                        'date': so.date_order,
                        'product': lines.product_id.name,
                        'quantity': lines.product_uom_qty,
                        'price': lines.product_id.list_price,
                        'subtotal': lines.price_subtotal,
                        'user': so.user_id.name,
                    }
                    result.append(res)

        datas = {
            'ids': self,
            'model': 'sale.order.salesperson',
            'form': result,
            'user_id': users,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'type': self.type,
            'no_value': False,

        }
        if self.from_date and self.to_date and not self.user_id and not self.product_ids:
            datas['no_value']=True
        return datas

    def get_report(self):
        datas = self._get_data()
        return self.env.ref('sale_order_salesperson.action_sale_report').report_action([], data=datas)

    def get_excel_report(self):
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.order.salesperson',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Excel Report Name',
                     },
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        record = []
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range('G2:L3', 'Sales Order Report', head)
        if data['start_date'] and data['end_date']:
            sheet.write('G6', 'From:', cell_format)
            sheet.merge_range('H6:I6', data['start_date'], txt)
            sheet.write('J6', 'To:', cell_format)
            sheet.merge_range('K6:L6', data['end_date'], txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center','bg_color':'#bbd5fc','border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#c0dbfa', 'border': 1})
        if data['type'] == 'user':
            record = data['user_id']
        h_row = 7
        h_col = 9
        count = 0
        row = 5
        col = 6
        row_number = 6
        t_row = 6
        if data['type'] == 'user':
            for rec in record:
                sheet.merge_range(h_row, h_col-3,h_row,h_col+2,rec['name'], format3)
                row = row + count + 3
                sheet.write(row, col, 'Order', format2)
                col += 1
                sheet.write(row, col, 'Date', format2)
                sheet.set_column('H:H', 15)
                col += 1
                if data['type'] == 'user':
                    sheet.write(row, col, 'Product', format2)
                    sheet.set_column('I:I', 20)
                    col += 1
                sheet.write(row, col, 'Quantity', format2)
                col += 1
                sheet.write(row, col, 'Price', format2)
                col += 1
                sheet.write(row, col, 'Subtotal', format2)
                col += 1
                col = 6
                count = 0
                row_number = row_number + count + 3
                t_subtotal = 0
                t_col = 6
                for val in data['form']:
                    if data['type'] == 'user':
                        if val['user_id'] == rec['id']:
                            count += 1
                            column_number = 6
                            sheet.write(row_number, column_number, val['sequence'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['date'], format1)
                            sheet.set_column('H:H', 15)
                            column_number += 1
                            sheet.write(row_number, column_number, val['product'], format1)
                            sheet.set_column('I:I', 20)
                            column_number += 1
                            sheet.write(row_number, column_number, val['quantity'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['price'], format1)
                            column_number += 1
                            sheet.write(row_number, column_number, val['subtotal'], format1)
                            t_subtotal += val['subtotal']
                            column_number += 1
                            row_number += 1
                t_row = t_row + count + 3
                t_col += 2
                sheet.write(t_row, t_col, 'Total', format4)
                t_col += 3
                sheet.write(t_row, t_col, t_subtotal, format4)
                t_col += 1
                h_row = h_row + count + 3
        if data['no_value'] == True:
            row += 3
            row_number += 2
            t_subtotal = 0
            t_col = 7
            sheet.write(row, col, 'Order', format2)
            col += 1
            sheet.write(row, col, 'Date', format2)
            sheet.set_column('H:H', 15)
            col += 1
            sheet.write(row, col, 'Salesperson', format2)
            sheet.set_column('I:I', 20)
            col += 1
            sheet.write(row, col, 'Product', format2)
            sheet.set_column('J:J', 20)
            col += 1
            sheet.write(row, col, 'Quantity', format2)
            col += 1
            sheet.write(row, col, 'Price', format2)
            col += 1
            sheet.write(row, col, 'Subtotal', format2)
            col += 1
            row_number+=1
            for val in data['form']:
                column_number = 6
                sheet.write(row_number, column_number, val['sequence'], format1)
                column_number += 1
                sheet.write(row_number, column_number, val['date'], format1)
                sheet.set_column('H:H', 15)
                column_number += 1
                sheet.write(row_number, column_number, val['user'], format1)
                sheet.set_column('I:I', 20)
                column_number += 1
                sheet.write(row_number, column_number, val['product'], format1)
                sheet.set_column('J:J', 20)
                column_number += 1
                sheet.write(row_number, column_number, val['quantity'], format1)
                column_number += 1
                sheet.write(row_number, column_number, val['price'], format1)
                column_number += 1
                sheet.write(row_number, column_number, val['subtotal'], format1)
                t_subtotal += val['subtotal']
                column_number += 1
                row_number += 1
            sheet.write(row_number, t_col, 'Total', format4)
            t_col += 4
            sheet.write(row_number, t_col, t_subtotal, format4)
            t_col += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
