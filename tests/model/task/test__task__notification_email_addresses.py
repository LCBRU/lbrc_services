def test__notification_email_addresses(client, faker):
    uo = faker.user().get(save=True)
    ur = faker.user().get(save=True)

    s = faker.service().get(save=True, owners=[uo], generic_recipients='')
    t = faker.task().get(save=True, service=s, requestor=ur)

    assert t.notification_email_addresses == [uo.email, ur.email]
