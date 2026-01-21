import pytest
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, ReportsPageTester


class ReportsTester:
    @property
    def endpoint(self):
        return 'ui.reports'


class TestReportsRequiresLogin(ReportsTester, RequiresLoginTester):
    ...


class TestUploadDeleteRequiresOwner(ReportsTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        u = self.faker.user().get(save=True)
        self.faker.service().get(save=True, owners=[u])
        return u

    @property
    def user_without_required_role(self):
        return self.faker.user().get(save=True)


class TestPackIndex(ReportsTester, ReportsPageTester):
    def test__get__no_filters(self):
        self.faker.service().get(save=True, owners=[self.loggedin_user])

        resp = self.get()
        self.assert_all(resp=resp)
