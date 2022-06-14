from faker.providers import BaseProvider
from lbrc_services.model.quotes import Quote, QuoteStatusType
from lbrc_services.model.services import Organisation, TaskData, TaskStatusType, ToDo, User, Service, Task, TaskFile
from lbrc_flask.database import db
from io import BytesIO
from pathlib import Path


class FakerFile():
    def __init__(self, content, filename):
        self.content = content
        self.filename = filename

    def file(self):
        return BytesIO(self.content.encode('utf-8'))

    def file_tuple(self):
        return (
            self.file(),
            self.filename
        )


class LbrcServicesFakerProvider(BaseProvider):
    def fake_file(self):
        return FakerFile(self.generator.text(), self.generator.file_name(extension='pdf'))

    def user_details(self):
        u = User(
            first_name=self.generator.first_name(),
            last_name=self.generator.last_name(),
            email=self.generator.email(),
            active=True,
        )
        return u

    def service_details(self, owners=None, name=None, field_group=None, generic_recipients=None, suppress_owner_email=False):
        if name is None:
            name = self.generator.pystr(min_chars=5, max_chars=10)

        if generic_recipients is None:
            generic_recipients = self.generator.email()

        if field_group is None:
            field_group = self.generator.field_group_details()

        result = Service(
            name=name,
            field_group=field_group,
            generic_recipients=generic_recipients,
            suppress_owner_email=suppress_owner_email,
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

    def quote_details(
        self,
        name=None,
        requestor=None,
        current_status_type=None,
        organisation=None,
        organisation_description=None,
        created_date=None,
    ):
        result = Quote()

        if current_status_type is None:
            result.current_status_type_id = QuoteStatusType.get_draft().id
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

        if requestor is None:
            result.requestor = self.user_details()
        elif requestor.id is None:
            result.requestor = requestor
        else:
            result.requestor_id = requestor.id

        if organisation_description is None:
            result.organisation_description = ''

        if created_date is not None:
            result.created_date = created_date

        return result

    def task_file_details(self, task=None, field=None, filename=None):

        if filename is None:
            filename = self.generator.pystr(min_chars=5, max_chars=10)

        result = TaskFile(
            filename=filename,
            local_filepath=self.generator.pystr(min_chars=5, max_chars=10),
        )

        if task is None:
            result.task = self.task_details()
        elif task.id is None:
            result.task = task
        else:
            result.task = task
            result.task_id = task.id

        if field is None:
            result.field = self.generator.field_details()
        elif field.id is None:
            result.field = field
        else:
            result.field_id = field.id

        return result

    def task_data_details(self, task=None, field=None, value=None):
        result = TaskData()

        if task is None:
            result.task = self.task_details()
        elif task.id is None:
            result.task = task
        else:
            result.task_id = task.id

        if field is None:
            result.field = self.generator.field_details()
        elif field.id is None:
            result.field = task
        else:
            result.field_id = field.id

        if value is None:
            result.value = self.generator.pystr(min_chars=5, max_chars=100)
        else:
            result.value = value
        
        return result

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

    def get_test_owned_task(self, owner, count=1, **kwargs):
        s = self.get_test_service(owners=[owner])
        r = None
        rs = []

        for _ in range(count):
            r = self.task_details(**kwargs, service=s)
            rs.append(r)

        db.session.add_all(rs)
        db.session.commit()

        return r


    def get_test_task(self, count=1, **kwargs):
        r = None
        rs = []

        for _ in range(count):
            r = self.task_details(**kwargs)
            rs.append(r)

        db.session.add_all(rs)

        db.session.commit()

        return r


    def get_test_quote(self, count=1, **kwargs):
        result = []

        for _ in range(count):
            r = self.quote_details(**kwargs)
            result.append(r)

        db.session.add_all(result)

        db.session.commit()

        return result


    def get_test_task_file(self, fake_file=None, **kwargs):
        r = self.task_file_details(**kwargs)

        if fake_file is None:
            fake_file = FakerFile(self.generator.text(), r.filename)

        filepath = r._new_local_filepath(r.filename)
        filepath.parents[0].mkdir(parents=True, exist_ok=True)
        r.local_filepath = str(filepath)
        f = open(filepath, "a")
        f.write(fake_file.content)
        f.close()

        db.session.add(r)
        db.session.commit()

        return r


    def get_test_service(self, **kwargs):
        rt = self.service_details(**kwargs)

        db.session.add(rt)
        db.session.commit()

        return rt


    def get_test_user(self, **kwargs):
        u = self.user_details(**kwargs)
        db.session.add(u)
        db.session.commit()

        return u


    def get_test_todo(self, **kwargs):
        t = self.todo_details(**kwargs)
        db.session.add(t)
        db.session.commit()

        return t

    def get_test_owned_todo(self, user, status_name=None):
        if status_name is None:
            status_name = ToDo.OUTSTANDING

        s = self.get_test_service(owners=[user])
        task = self.get_test_task(service=s)
        todo = self.get_test_todo(task=task, status=ToDo.get_status_code_from_name(status_name))

        return todo


    def get_test_field_of_type(self, field_type, choices=None):
        fg = self.generator.get_test_field_group()
        s = self.get_test_service(field_group=fg)
        f = self.generator.get_test_field(field_group=fg, field_type=field_type, choices=choices)
        return s,f


    def get_test_task_data(self, **kwargs):
        td = self.task_data_details(**kwargs)
        db.session.add(td)
        db.session.commit()

        return td

