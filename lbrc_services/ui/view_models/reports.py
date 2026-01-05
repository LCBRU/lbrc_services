from datetime import datetime
from lbrc_flask.database import db
from lbrc_flask.charting import BarChart, BarChartItem
from lbrc_flask.forms.dynamic import Field
from sqlalchemy import func, literal_column, select
from lbrc_services.model.services import Organisation, Task, TaskData, TaskStatusType
from lbrc_services.services.tasks import task_search_query
from dateutil import rrule


class Report:
    def __init__(self, search_form):
        self.search_form = search_form

    def get_report_name(self):
        return f'Jobs by {self.report_grouper_name}'

    @property
    def report_grouper_name(self):
        ...

    def get_chart(self):
        group_category = self.get_chart_items()

        bc: BarChart = BarChart(
            title=self.get_report_name(),
            items=group_category,
            y_title='Jobs',
        )

        return bc

    def get_report_name(self):
        ...

    def get_chart_items(self):
        ...


class MonthRequestedReport(Report):
    @property
    def report_grouper_name(self):
        return 'Month Requested'

    def get_chart_items(self):
        q_tasks = task_search_query(self.search_form.data).cte('q_tasks')

        min_max_date = db.session.execute(
            select(
                func.min(q_tasks.c.created_date),
                func.max(q_tasks.c.created_date),
            )
        ).mappings().one()

        min_date = min_max_date['min']
        min_date = datetime(min_date.year, min_date.month, 1)

        default_monthly_totals = {
            f'{dt:%Y-%m}': BarChartItem(
                series='Month Requested',
                bucket=f'{dt:%Y-%m}',
                count=0,
            ) for dt in rrule.rrule(rrule.MONTHLY, dtstart=min_date, until=min_max_date['max'])
        }

        year_month = func.date_format(q_tasks.c.created_date, '%Y-%m')

        q_year_month_counts = (
            select(
                year_month.label('bucket'),
                func.count().label('count'),
            )
            .group_by(year_month)
            .order_by(year_month)
        )

        for row in db.session.execute(q_year_month_counts).mappings().all():
            default_monthly_totals[row['bucket']].count = row['count']

        return default_monthly_totals.values()


class CurrentStatusReport(Report):
    @property
    def report_grouper_name(self):
        return 'Current Status'

    def get_chart_items(self):
        q_tasks = task_search_query(self.search_form.data).cte('q_tasks')

        q_year_month_counts = (
            select(
                TaskStatusType.name.label('bucket'),
                literal_column("'Current Status'").label('series'),
                func.count().label('count'),
            )
            .select_from(q_tasks)
            .join(TaskStatusType, TaskStatusType.id == q_tasks.c.current_status_type_id)
            .group_by(q_tasks.c.current_status_type_id)
            .order_by(q_tasks.c.current_status_type_id)
        )

        return db.session.execute(q_year_month_counts).mappings().all()


class OrganisationReport(Report):
    @property
    def report_grouper_name(self):
        return 'Organisation'

    def get_chart_items(self):
        q_tasks = task_search_query(self.search_form.data).cte('q_tasks')
        q_task_orgs = (
            select(
                q_tasks.c.id.label('task_id'),
                Organisation.name.label('organisation_name'),
            )
            .join(Organisation, Organisation.tasks.any(Task.id == q_tasks.c.id))
        ).cte('q_task_orgs')

        q_year_month_counts = (
            select(
                q_task_orgs.c.organisation_name.label('bucket'),
                literal_column("'Organisation'").label('series'),
                func.count().label('count'),
            )
            .group_by(q_task_orgs.c.organisation_name)
            .order_by(q_task_orgs.c.organisation_name)
        )

        return db.session.execute(q_year_month_counts).mappings().all()


class FieldReport(Report):
    def __init__(self, search_form, field_id):
        super().__init__(search_form)
        self.field_id = field_id

    @property
    def report_grouper_name(self):
        field = db.get_or_404(Field, self.field_id)
        return field.get_label()

    def get_chart_items(self):
        q_tasks = task_search_query(self.search_form.data).cte('q_tasks')
        q_task_field_values = (
            select(
                q_tasks.c.id.label('task_id'),
                TaskData.value.label('value'),
                Field.field_name.label('field_name'),
            )
            .join(Task, Task.id == q_tasks.c.id)
            .join(Task.data)
            .join(TaskData.field)
            .where(TaskData.field_id == self.field_id)
        ).cte('q_task_field_values')

        q_value_counts = (
            select(
                q_task_field_values.c.value.label('bucket'),
                q_task_field_values.c.field_name.label('series'),
                func.count().label('count'),
            )
            .group_by(q_task_field_values.c.value)
            .order_by(q_task_field_values.c.value)
        )

        return db.session.execute(q_value_counts).mappings().all()
