def test__suppress_owner_email__true(client, faker):
    u = faker.get_test_user()

    s = faker.get_test_service(owners=[u], generic_recipients='test@example.com', suppress_owner_email=True)

    assert s.notification_email_addresses == ['test@example.com']


def test__suppress_owner_email__false(client, faker):
    u = faker.get_test_user()

    s = faker.get_test_service(owners=[u], generic_recipients='test@example.com', suppress_owner_email=False)

    assert s.notification_email_addresses == [u.email, 'test@example.com']
