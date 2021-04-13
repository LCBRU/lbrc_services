def test__notification_email_addresses(client, faker):
    uo = faker.get_test_user()
    ur = faker.get_test_user()

    s = faker.get_test_service(owners=[uo], generic_recipients='')
    t = faker.get_test_task(service=s, requestor=ur)

    assert t.notification_email_addresses == [uo.email, ur.email]
