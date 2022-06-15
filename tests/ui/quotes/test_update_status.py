from flask_api import status
from flask import url_for
from lbrc_services.model.quotes import QuoteStatus, QuoteStatusType
from lbrc_services.model.services import TaskStatus, TaskStatusType
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.quote_update_status', _external=external, **kwargs)


def _update_status_post(client, quote, status, notes):
    return client.post(
        _url(),
        data={
            'quote_id': quote.id,
            'status': status.id,
            'notes': notes,
        },
    )


def test__post__requires_login(client):
    assert__requires_login(client, _url(external=False), post=True)


def test__quote__update_status(client, faker, loggedin_user):
    quote = faker.get_test_quote()

    sq = QuoteStatusType.get_awaiting_approval()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, quote, sq, notes)

    assert QuoteStatus.query.filter(QuoteStatus.quote_id == quote.id).count() == 1
    qs = QuoteStatus.query.filter(QuoteStatus.quote_id == quote.id).one()
    assert qs.quote_status_type_id == sq.id
    assert qs.quote_id == quote.id
    assert qs.notes == notes
