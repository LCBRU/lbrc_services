def test__notification_email_addresses(client, faker):
    uo = faker.user().get_in_db()
    ur = faker.user().get_in_db()

    s = faker.service().get_in_db(owners=[uo], generic_recipients='')
    t = faker.task().get_in_db(service=s, requestor=ur)

    assert t.notification_email_addresses == [uo.email, ur.email]
