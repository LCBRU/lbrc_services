# LBRC Services

Site for BRC staff to make requests for BRC central services, such as
comms, PPI and IT.

## Installation and Running

1. Download the code from github

```bash
git clone git@github.com:LCBRU/lbrc_services.git
```

2. Install the requirements

Go to the `lbrc_services` directory and type the command:

```bash
pip install -r requirements.txt
```

3. Create the database using

Staying in the `lbrc_services` directory and type the command:

```bash
python create_test_db.py
```

4. Run the application

Staying in the `lbrc_services` directory and type the command:

```bash
./app.py
```

## Development

### Installation

To test the application, run the following command from the project folder:

```bash
pip install -r requirements-dev.txt
```

### Testing

To test the application, run the following command from the project folder:

```bash
pytest
```

### Database Schema Amendments

#### Create Migration

To create a migration run the command

```bash
./manage.py script "{Description of change}"
```

You will then need to change the newly-created script created in the
`migrations` directory to make the necessary upgrade and downgrade
changes.

#### Apply Migrations to Database

After amending the models, run the following command to create the
migrations and apply them to the database:

```bash
./manage.py upgrade
```

## Deployment

### Database

The database upgrades are handled by SQLAlchemy-migrate and are run using the `manage.py` program
once the configuration has been copied into place and the database created.

First create an empty database in the database server, then initialise the migrations by running the command:

```bash
manage.py version_control
manage.py upgrade
```

#### Upgrade

To upgrade the database to the current version, run the command:

```bash
manage.py upgrade
```
