# Matna Visibility Platform - Backend

## Stack
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication

## Setup

### 1. Create virtual environment
python -m venv venv

### 2. Activate
Windows:
venv\Scripts\activate

Linux/macOS:
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements/development.txt

### 4. Configure environment
Copy `.env.example` to `.env` and update values.

### 5. Run migrations
python manage.py makemigrations
python manage.py migrate

### 6. Create superuser
python manage.py createsuperuser

### 7. Run server
python manage.py runserver

## API Docs
- /api/docs/
- /api/schema/

## Important Endpoints

### Auth
- POST /api/auth/login/
- POST /api/auth/refresh/
- GET /api/auth/me/

### Users
- GET /api/users/
- POST /api/users/

### Production
- GET /api/production/entries/
- POST /api/production/entries/

### Suppliers
- GET /api/suppliers/
- POST /api/suppliers/
- GET /api/suppliers/deliveries/
- POST /api/suppliers/deliveries/

### Inventory
- GET /api/inventory/items/
- GET /api/inventory/balances/
- GET /api/inventory/transactions/

### Analytics
- GET /api/analytics/dashboard/
- GET /api/analytics/summary/?period=daily
- GET /api/analytics/yield-trend/
- GET /api/analytics/inflow-vs-output/
- GET /api/analytics/downtime-trend/
- GET /api/analytics/reports/export/csv/?period=weekly
- GET /api/analytics/reports/export/pdf/?period=monthly