from flask import render_template
from flask_security import roles_accepted
from sqlalchemy import select
from lbrc_services.model.security import ROLE_EXPORTER
from lbrc_services.model.services import Service, Task
from lbrc_services.ui.views import send_task_export
from lbrc_flask.formatters import format_datetime, format_yesno
from lbrc_flask.export import excel_download
from lbrc_flask.database import db
from .. import blueprint


@blueprint.route("/export")
@roles_accepted('exporter')
def export():
    return send_task_export('All Tasks', Task.query.all())


@blueprint.route("/exports")
def exports():
    return render_template(
        "ui/export/index.html",
    )


@blueprint.route("/export_ppi")
def export_ppi():
    services = db.session.execute(select(Service)).unique().scalars()
    ppie_service = next((s for s in services if s.is_ppie), None)
    tasks = db.session.execute(select(Task).where(Task.service == ppie_service)).unique().scalars()
    return send_task_export('PPIE Tasks', tasks)


def send_task_export(title, tasks):
    # Use of dictionary instead of set to maintain order of headers
    headers = {
        'request_date': None,
        'deadline': None,
        'organisation': None,
        'pi': None,
        'requestor': None,
        'requestor_email': None,
        'study': None,
        'objectives': None,
        'summary': None,
        'plain_english_summary': None,
        'purpose': None,
        'ppie_required_focus_group_online': None,
        'ppie_required_focus_group_face_to_face': None,
        'ppie_required_dance_and_health': None,
        'ppie_required_event': None,
        'ppie_required_other_arts': None,
        'ppie_required_bid_writing': None,
        'ppie_funded': None,
        'ppie_funding_body': None,
        'bid_expected_outcome_date': None,
        'bid_funder': None,
        'bid_funding_call': None,
    }

    task_details = []

    for t in tasks:
        td = {}
        task_details.append(td)

        td['request_date'] = format_datetime(t.created_date)
        td['deadline'] = t.get_value_for_field_name('deadline')
        td['organisation'] = t.organisations_joined()
        td['pi'] = t.get_value_for_field_name('pi')
        td['requestor'] = t.requestor.full_name
        td['requestor_email'] = t.requestor.email
        td['study'] = t.get_value_for_field_name('study')
        td['objectives'] = '; '.join([d.formated_value for d in t.data if d.field.field_name == 'objectives'])
        td['summary'] = t.get_value_for_field_name('summary')
        td['plain_english_summary'] = t.get_value_for_field_name('plain_english_summary')
        td['purpose'] = t.get_value_for_field_name('purpose')

        requirements = [d.formated_value for d in t.data]

        td['ppie_required_focus_group_online'] = format_yesno('Focus group-on line' in requirements)
        td['ppie_required_focus_group_face_to_face'] = format_yesno('Focus group-face to face' in requirements)
        td['ppie_required_dance_and_health'] = format_yesno('Dance and Health' in requirements)
        td['ppie_required_event'] = format_yesno('Event' in requirements)
        td['ppie_required_other_arts'] = format_yesno('Other arts based approach' in requirements)
        td['ppie_required_bid_writing'] = format_yesno('Bid Writing' in requirements)
        td['ppie_funded'] = t.get_value_for_field_name('ppie_funded')
        td['ppie_funding_body'] = t.get_value_for_field_name('ppie_funding_body')
        td['bid_expected_outcome_date'] = t.get_value_for_field_name('bid_expected_outcome_date')
        td['bid_funder'] = t.get_value_for_field_name('bid_funder')
        td['bid_funding_call'] = t.get_value_for_field_name('bid_funding_call')
        
    return excel_download(title, headers.keys(), task_details)


