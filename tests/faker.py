from faker.providers import BaseProvider
from lbrc_requests.model import RequestStatusType, User, RequestType, Request, RequestFile


class LbrcRequestsFakerProvider(BaseProvider):
    def user_details(self):
        u = User(
            first_name=self.generator.first_name(),
            last_name=self.generator.last_name(),
            email=self.generator.email(),
            active=True,
        )
        return u

    def request_type_details(self, owners=None):
        result = RequestType(
            name=self.generator.pystr(min_chars=5, max_chars=10),
            field_group=self.generator.field_group_details(),
        )

        result.owners = owners or []

        return result


    def request_details(self, name=None, request_type=None, requestor=None, current_status_type=None):
        if name is None:
            name = self.generator.pystr(min_chars=5, max_chars=10)

        if request_type is None:
            request_type = self.request_type_details()
        
        if requestor is None:
            requestor = self.user_details()

        if current_status_type is None:
            current_status_type = RequestStatusType.get_created()

        return Request(
            name=name,
            request_type=request_type,
            requestor=requestor,
            current_status_type=current_status_type,
        )

    def request_file_details(self, request=None):
        if request is None:
            request = self.request_details()

        return RequestFile(
            filename=self.generator.pystr(min_chars=5, max_chars=10),
            local_filepath=self.generator.pystr(min_chars=5, max_chars=10),
            request=request,
            field=self.generator.field_details()
        )
