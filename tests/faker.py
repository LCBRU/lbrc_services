from faker.providers import BaseProvider
from lbrc_services.model import Organisation, TaskStatusType, ToDo, User, Service, Task, TaskFile


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


    def task_details(
        self,
        name=None,
        service=None,
        requestor=None,
        current_status_type=None,
        organisation=None,
        organisation_description=None,
    ):
        result = Task()

        if current_status_type is None:
            result.current_status_type_id = TaskStatusType.get_created().id
        else:
            result.current_status_type_id = current_status_type.id

        if organisation is None:
            result.organisation_id = Organisation.get_organisation(Organisation.CARDIOVASCULAR).id
        else:
            result.organisation_id = organisation.id

        if name is None:
            result.name = self.generator.pystr(min_chars=5, max_chars=10)
        else:
            result.name = name

        if service is None:
            result.service = self.service_details()
        elif service.id is None:
            result.service = service
        else:
            result.service_id = service.id
        
        if requestor is None:
            result.requestor = self.user_details()
        elif requestor.id is None:
            result.requestor = requestor
        else:
            result.requestor_id = requestor.id

        if organisation_description is None:
            result.organisation_description = ''

        return result

    def task_file_details(self, task=None):
        if task is None:
            task = self.task_details()

        return TaskFile(
            filename=self.generator.pystr(min_chars=5, max_chars=10),
            local_filepath=self.generator.pystr(min_chars=5, max_chars=10),
            task=task,
            field=self.generator.field_details()
        )

    def todo_details(self, task=None, description=None, status=None):
        if task is None:
            task = self.task_details()

        if description is None:
            description = self.generator.pystr(min_chars=5, max_chars=100)

        return ToDo(
            task=task,
            description=description,
            status=status,
        )
