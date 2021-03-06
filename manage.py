#!/usr/bin/env python

import os

from flask_migrate import MigrateCommand
from flask_script import Manager, Server
from flask_script.commands import ShowUrls, Clean

from app import create_app
from app.extensions import db
from app.models.bi import BIImportConfig, BIStatistic, BIUser, BIUserCurrency, BIUserBill, BIClubWPTUser
from app.models.main import AdminUser, AdminUserActivity, AdminUserQuery
from app.tasks.bi_clubwpt_user import process_bi_clubwpt_user
from app.tasks.bi_statistic import process_bi_statistic
from app.tasks.bi_user import process_bi_user
from app.tasks.bi_user_bill import process_bi_user_bill
from app.tasks.bi_user_currency import process_bi_user_currency
from app.tasks.scheduled import process_bi
from flask_assets import ManageAssets
from app.asset import assets
# default to dev config because no one should use this in
# production anyway
env = os.environ.get('WPT_DWH_ENV', 'dev')
app = create_app('app.settings.%sConfig' % env.capitalize())


manager = Manager(app)
manager.add_command("server", Server(host='0.0.0.0'))
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())
manager.add_command('db', MigrateCommand)
manager.add_command("assets", ManageAssets(assets))
#./manage.py assets rebuild


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
        in the context of the app
    """

    return dict(app=app, db=db, AdminUser=AdminUser)


def init_bi_user_import_config():
    """ Init BIImportConfig Table """

    BIImportConfig.__table__.create(db.engine, checkfirst=True)

    variables = ['last_imported_user_id',
                 'last_imported_user_update_time',
                 'last_imported_user_billing_info_id',
                 'last_imported_user_info_add_time',
                 'last_imported_user_info_update_time',
                 'last_imported_user_login_time',
                 'last_imported_user_ourgame_add_time',
                 'last_imported_user_ourgame_update_time',
                 'last_imported_user_payment_spin_purchase_add_time',
                 'last_imported_user_payment_spin_purchase_update_time',
                 'last_imported_user_mall_order_add_time',
                 'last_imported_user_mall_order_update_time',
                 'last_imported_og_powergamecoin_add_time',
                 'last_imported_og_gamecoin_add_time']

    for v in variables:
        db.session.query(BIImportConfig).filter_by(var=v).delete()
        db.session.add(BIImportConfig(var=v))

    db.session.commit()


def init_bi_user_bill_import_config():
    """ Init BIImportConfig Table """

    BIImportConfig.__table__.create(db.engine, checkfirst=True)

    variables = ['last_imported_user_bill_dollar_paid_add_time',
                 'last_imported_user_mall_bill_order_id',
                 'last_imported_user_mall_bill_order_update_time',
                 'last_imported_user_payment_bill_order_id']

    for v in variables:
        db.session.query(BIImportConfig).filter_by(var=v).delete()
        db.session.add(BIImportConfig(var=v))

    db.session.commit()


def init_bi_user_currency_import_config():
    """ Init BIImportConfig Table """

    BIImportConfig.__table__.create(db.engine, checkfirst=True)

    variables = ['last_imported_user_gold_currency_add_time',
                 'last_imported_user_silver_currency_add_time']

    for v in variables:
        db.session.query(BIImportConfig).filter_by(var=v).delete()
        db.session.add(BIImportConfig(var=v))

    db.session.commit()


def init_bi_clubwpt_user_import_config():
    """ Init BIImportConfig Table """

    BIImportConfig.__table__.create(db.engine, checkfirst=True)

    variables = ['last_imported_clubwpt_user_add_time',
                 'last_imported_clubwpt_user_update_time']

    for v in variables:
        db.session.query(BIImportConfig).filter_by(var=v).delete()
        db.session.add(BIImportConfig(var=v))

    db.session.commit()


@manager.command
def reset_bi():
    """ ReCreate Database and Seed """

    db.drop_all(bind=None)
    db.create_all(bind=None)

    init_bi_user_import_config()
    init_bi_user_bill_import_config()
    init_bi_user_currency_import_config()
    init_bi_clubwpt_user_import_config()

    user = AdminUser(email='admin@admin.com', password='password', timezone='EST')
    user.name = "Test Account"
    db.session.add(user)

    user = AdminUser(email='admin1@admin.com', password='password', timezone='EST')
    user.name = "Test1 Account"
    db.session.add(user)

    db.session.commit()


@manager.command
def reset_bi_admin():
    """ ReCreate Database and Seed """

    AdminUserActivity.__table__.drop(db.engine, checkfirst=True)
    AdminUserQuery.__table__.drop(db.engine, checkfirst=True)

    AdminUserActivity.__table__.create(db.engine, checkfirst=True)
    AdminUserQuery.__table__.create(db.engine, checkfirst=True)


@manager.command
def reset_bi_user():
    """ ReCreate Database and Seed """

    BIUser.__table__.drop(db.engine, checkfirst=True)

    BIUser.__table__.create(db.engine, checkfirst=True)

    init_bi_user_import_config()


@manager.command
def reset_bi_user_bill():
    """ ReCreate Database and Seed """

    BIUserBill.__table__.drop(db.engine, checkfirst=True)

    BIUserBill.__table__.create(db.engine, checkfirst=True)

    init_bi_user_bill_import_config()


@manager.command
def reset_bi_user_currency():
    """ ReCreate Database and Seed """

    BIUserCurrency.__table__.drop(db.engine, checkfirst=True)

    BIUserCurrency.__table__.create(db.engine, checkfirst=True)

    init_bi_user_currency_import_config()


@manager.command
def reset_bi_clubwpt_user():
    """ ReCreate Database and Seed """

    BIClubWPTUser.__table__.drop(db.engine, checkfirst=True)

    BIClubWPTUser.__table__.create(db.engine, checkfirst=True)

    init_bi_clubwpt_user_import_config()


@manager.command
def reset_bi_statistic():
    """ ReCreate Database and Seed """

    BIStatistic.__table__.drop(db.engine, checkfirst=True)

    BIStatistic.__table__.create(db.engine, checkfirst=True)

    from datetime import date
    import pandas as pd
    for day in pd.date_range(date(2016, 6, 1), date(2017, 12, 31)):
        for game in ['All Game', 'Texas Poker', 'TimeSlots']:
            for platform in ['All Platform', 'iOS', 'Android', 'Web', 'Facebook Game']:
                db.session.add(BIStatistic(day=day.strftime("%Y-%m-%d"), game=game, platform=platform))
    db.session.commit()


@manager.command
def sync_bi():
    if app.config['ENV'] == 'prod':
        process_bi.delay()
    else:
        process_bi()


@manager.command
def sync_bi_user():
    if app.config['ENV'] == 'prod':
        process_bi_user.delay()
    else:
        process_bi_user()


@manager.command
def sync_bi_user_bill():
    if app.config['ENV'] == 'prod':
        process_bi_user_bill.delay()
    else:
        process_bi_user_bill()


@manager.command
def sync_bi_user_currency():
    if app.config['ENV'] == 'prod':
        process_bi_user_currency.delay()
    else:
        process_bi_user_currency()


@manager.command
def sync_bi_clubwpt_user():
    if app.config['ENV'] == 'prod':
        process_bi_clubwpt_user.delay()
    else:
        process_bi_clubwpt_user()


@manager.command
def sync_bi_statistic_for_lifetime():
    if app.config['ENV'] == 'prod':
        process_bi_statistic.delay('lifetime')
    else:
        process_bi_statistic('lifetime')


@manager.command
def sync_bi_statistic_for_yesterday():
    if app.config['ENV'] == 'prod':
        process_bi_statistic.delay('yesterday')
    else:
        process_bi_statistic('yesterday')


@manager.command
def process_bi_statistic_for_today():
    if app.config['ENV'] == 'prod':
        process_bi_statistic.delay('today')
    else:
        process_bi_statistic('today')


@manager.command
def preset_cache():
    if __name__ == "__main__":
        manager.run()
