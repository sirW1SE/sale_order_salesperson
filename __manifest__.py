# -*- coding: utf-8 -*-

{
    'name': 'Sale Order Report',
    'version': '14.0.1.0.0',
    'summary': 'ODOO 14 Sale Order',
    'description': """PDF and Excel""",
    'author': 'Solatorio',
    'company': 'MUTI',
    'maintainer': 'wise',
    'category': 'Sales',
    'website': '',
    'depends': ['sale_management', 'base','account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_report.xml',
        'views/report_view.xml',
        'views/action_manager.xml',
        'report/sale_reports.xml',
        'report/sale_profit_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
