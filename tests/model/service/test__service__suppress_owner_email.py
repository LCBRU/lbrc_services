def test__suppress_owner_email__true(client, faker):
    u = faker.user().get(save=True)

    s = faker.service().get(save=True, owners=[u], generic_recipients='test@example.com', suppress_owner_email=True)

    assert s.notification_email_addresses == ['test@example.com']


def test__suppress_owner_email__false(client, faker):
    u = faker.user().get(save=True)

    s = faker.service().get(save=True, owners=[u], generic_recipients='test@example.com', suppress_owner_email=False)

    assert s.notification_email_addresses == [u.email, 'test@example.com']
