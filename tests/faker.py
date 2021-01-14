from faker.providers import BaseProvider
from lbrc_services.model import RequestStatusType, User, Service, Task, TaskFile


class LbrcServicesFakerProvider(BaseProvider):
    def user_details(self):
        u = User(
            first_name=self.generator.first_name(),
            last_name=self.generator.last_name(),
            email=self.generator.email(),
            active=True,
        )
        return u

    def service_details(self, owners=None, name=None, field_group=None):
        if name is None:
            name = self.generator.pystr(min_chars=5, max_chars=10)

        if field_group is None:
            field_group = self.generator.field_group_details()

        result = Service(
            name=name,
            field_group=field_group,
        )

        result.owners = owners or []

        return result


    def task_details(self, name=None, service=None, requestor=None, current_status_type=None):
        if name is None:
            name = self.generator.pystr(min_chars=5, max_chars=10)

        if service is None:
            service = self.service_details()
        
        if requestor is None:
            requestor = self.user_details()

        if current_status_type is None:
            current_status_type = TaskStatusType.get_created()

        return Task(
            name=name,
            service=service,
            requestor=requestor,
            current_status_type=current_status_type,
        )

    def task_file_details(self, task=None):
        if task is None:
            task = self.task_details()

        return TaskFile(
            filename=self.generator.pystr(min_chars=5, max_chars=10),
            local_filepath=self.generator.pystr(min_chars=5, max_chars=10),
            task=task,
            field=self.generator.field_details()
        )
