from datetime import datetime
from functools import cache
from random import choice
from typing import Optional
from faker.providers import BaseProvider
from lbrc_services.model.quotes import Quote, QuotePricingType, QuoteStatusType
from lbrc_services.model.services import Organisation, TaskData, TaskStatusType, ToDo, User, Service, Task, TaskFile
from lbrc_flask.database import db
from lbrc_flask.pytest.faker import UserCreator as BaseUserCreator, FakeCreator
from io import BytesIO
from lbrc_flask.forms.dynamic import FieldType


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


class UserCreator(BaseUserCreator):
    cls = User


class ServiceCreator(FakeCreator):
    cls = Service

    def get(self, **kwargs):
        if (name := kwargs.get('name')) is None:
            name = self.faker.company()
        if (generic_recipients := kwargs.get('generic_recipients')) is None:
            generic_recipients = self.faker.email()
        if (field_group := kwargs.get('field_group')) is None:
            field_group = self.faker.field_group().get()
        if (suppress_owner_email := kwargs.get('suppress_owner_email')) is None:
            suppress_owner_email = False
        if (owners := kwargs.get('owners')) is None:
            owners = []

        return Service(
            name=name,
            generic_recipients=generic_recipients,
            field_group=field_group,
            suppress_owner_email=suppress_owner_email,
            owners=owners,
        )


class OrganisationCreator(FakeCreator):
    cls = Organisation

    def get(self, **kwargs):
        if (name := kwargs.get('name')) is None:
            name = self.faker.pystr(min_chars=5, max_chars=10)

        return Organisation(name=name)

class TaskCreator(FakeCreator):
    cls = Task

    def get(self, **kwargs):
        if (name := kwargs.get('name')) is None:
            name = self.faker.pystr(min_chars=5, max_chars=10)
        if (service := kwargs.get('service')) is None:
            service = self.faker.service().get()
            service_id = None
        else:
            service_id = service.id
        if (requestor := kwargs.get('requestor')) is None:
            requestor = self.faker.user().get()
        if (current_status_type := kwargs.get('current_status_type')) is None:
            current_status_type = TaskStatusType.get_created()
        if (organisation := kwargs.get('organisation')) is None:
            organisation = self.faker.organisation().get()
        if (organisation_description := kwargs.get('organisation_description')) is None:
            organisation_description = ''

        return Task(
            name=name,
            service=service,
            service_id=service_id,
            requestor=requestor,
            current_status_type_id=current_status_type.id,
            organisations=[organisation],
            organisation_description=organisation_description,
        )


class QuoteCreator(FakeCreator):
    cls = Quote

    def get(self, **kwargs):
        if (name := kwargs.get('name')) is None:
            name = self.faker.pystr(min_chars=5, max_chars=10)
        if (requestor := kwargs.get('requestor')) is None:
            requestor = self.faker.user().get()
        if (current_status_type := kwargs.get('current_status_type')) is None:
            current_status_type = QuoteStatusType.get_draft()
        if (organisation := kwargs.get('organisation')) is None:
            organisation = Organisation.get_organisation(Organisation.CARDIOVASCULAR)
        if (organisation_description := kwargs.get('organisation_description')) is None:
            organisation_description = ''
        if (quote_price_type := kwargs.get('quote_price_type')) is None:
            quote_price_type = QuotePricingType.query.first()
        if (created_date := kwargs.get('created_date')) is None:
            created_date = None
        if (date_requested := kwargs.get('date_requested')) is None:
            date_requested = datetime.now().date()

        return Quote(
            name=name,
            requestor=requestor,
            current_status_type=current_status_type,
            organisation_id=organisation.id,
            organisation_description=organisation_description,
            quote_pricing_type_id=quote_price_type.id,
            created_date=created_date,
            date_requested=date_requested,
        )


class TaskFileCreator(FakeCreator):
    cls = TaskFile

    def get(self, **kwargs):
        if (filename := kwargs.get('filename')) is None:
            filename = self.faker.pystr(min_chars=5, max_chars=10)
        if (local_filepath := kwargs.get('local_filepath')) is None:
            local_filepath = self.faker.pystr(min_chars=5, max_chars=10)
        if (task := kwargs.get('task')) is None:
            task = self.faker.task().get()
        if (field := kwargs.get('field')) is None:
            field = self.faker.field().get()

        return TaskFile(
            filename=filename,
            local_filepath=local_filepath,
            task=task,
            field=field,
        )


class TaskDataCreator(FakeCreator):
    cls = TaskData

    def get(self, **kwargs):
        if (task := kwargs.get('task')) is None:
            task = self.faker.task().get()

        if (field := kwargs.get('field')) is None:
            field_type_name = choice(FieldType.all_simple_field_types())
            field_type = FieldType._get_field_type(field_type_name)
            field = self.faker.field().get(field_type=field_type)

        if (value := kwargs.get('value')) is None:
            value = self.faker.pystr(min_chars=5, max_chars=10).upper()

        return TaskData(
            task=task,
            field=field,
            value=value,
        )


class ToDoCreator(FakeCreator):
    cls = ToDo

    def get(self, **kwargs):
        if (task := kwargs.get('task')) is None:
            task = self.faker.task().get()

        if (description := kwargs.get('description')) is None:
            description = self.faker.pystr(min_chars=5, max_chars=100)

        if (status := kwargs.get('status')) is None:
            status = None

        return ToDo(
            task=task,
            description=description,
            status=status,
        )


class LbrcServicesProvider(BaseProvider):
    def fake_file(self):
        return FakerFile(self.generator.text(), self.generator.file_name(extension='pdf'))

    @cache
    def user(self):
        return UserCreator(self)

    @cache
    def service(self):
        return ServiceCreator(self)
    
    @cache
    def task(self):
        return TaskCreator(self)

    @cache
    def quote(self):
        return QuoteCreator(self)

    @cache
    def task_file(self):
        return TaskFileCreator(self)
    
    def create_task_file_in_filesystem(self, task_file: TaskFile, fake_file: Optional[FakerFile] = None):
        if fake_file is None:
            fake_file = FakerFile(self.generator.text(), task_file.filename)

        filepath = task_file._new_local_filepath(task_file.filename)
        filepath.parents[0].mkdir(parents=True, exist_ok=True)
        task_file.local_filepath = str(filepath)
        f = open(filepath, "a")
        f.write(fake_file.content)
        f.close()

    @cache
    def task_data(self):
        return TaskDataCreator(self)

    def get_test_field_of_type(self, field_type, choices=None, allowed_file_extensions=None):
        s = self.service().get_in_db()
        f = self.generator.field().get_in_db(field_group=s.field_group, field_type=field_type, choices=choices, allowed_file_extensions='pdf')
        return s,f

    @cache
    def todo(self):
        return ToDoCreator(self)

    @cache
    def organisation(self):
        return OrganisationCreator(self)
