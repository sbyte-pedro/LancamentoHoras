# LancamentoHoras

Django web application for querying and exporting work hours from a back-office MySQL database into Excel reports.

## Requirements

- Python 3.11+
- Access to the MySQL `back_office` database (see [Database Configuration](#database-configuration))

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd LancamentoHoras
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file with credentials

Copy the example file and fill in the real values:

```bash
cp .env.example .env
```

Then edit `.env`:

```
SECRET_KEY=<generate a random key, e.g. with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DB_HOST=10.1.1.108
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=back_office
```

> `.env` is listed in `.gitignore` and must never be committed.

### 5. Apply Django migrations

This creates the local SQLite database used for authentication and sessions:

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username and password. These credentials are used to log into the application.

### 7. Run the development server

```bash
python manage.py runserver
```

The application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Usage

1. Open the browser at `http://127.0.0.1:8000`
2. You will be redirected to the login page — use the superuser credentials created above
3. Fill in the filter form (date range, collaborator codes, client, activity, cost center)
4. Click **Exportar Atividade** to download the Excel report

The JSON API endpoint is available at:

```
GET /api/backOfficeData?dataInicio=YYYYMMDD&dataFim=YYYYMMDD
```

---

## Project Structure

```
LancamentoHoras/
├── AtividadeApp/           # Main Django app (views, forms, templates)
│   ├── forms.py            # FiltrosForm — filter parameters for the query
│   ├── views.py            # main, login_view, logout_view, api_get_data_view
│   └── templates/          # HTML templates
├── backOfficeProject/      # Django project settings and URL configuration
├── services/               # Business logic (DB query, Excel and JSON generation)
│   ├── selectData.py       # MySQL query
│   ├── defToExcel.py       # DataFrame transformation + Excel workbook generation
│   ├── defToJson.py        # DataFrame transformation + JSON serialization
│   └── utils.py            # Time conversion helper (HH:MM → decimal)
├── base_static/css/        # Custom CSS
├── manage.py
└── requirements.txt
```

---

## Running Tests

```bash
python manage.py test
```
