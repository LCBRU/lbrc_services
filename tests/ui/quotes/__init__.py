from lbrc_services.model.quotes import Quote, QuoteStatusType


def _get_actual_quote():
    actuals = Quote.query.all()
    assert len(actuals) == 1
    return actuals[0]   


def assert__quote(expected, user):
    a = _get_actual_quote()

    assert a.name == expected.name
    assert a.organisation_id == expected.organisation_id
    assert a.organisation_description == expected.organisation_description
    assert a.requestor == user
    assert a.current_status_type == QuoteStatusType.get_draft()

    assert len(a.status_history) == 1
    s = a.status_history[0]
    assert s.quote == a
    assert len(s.notes) > 0
    assert s.quote_status_type == QuoteStatusType.get_draft()


def post_quote(client, url, quote):
    data={
        'name': quote.name,
        'organisation_id': quote.organisation_id,
        'organisation_description': quote.organisation_description,
        'quote_pricing_type_id': quote.quote_pricing_type_id,
        'date_requested': quote.date_requested,
    }

    if quote.requestor_id:
        data['requestor_id'] = quote.requestor_id

    return client.post(url, data=data)
