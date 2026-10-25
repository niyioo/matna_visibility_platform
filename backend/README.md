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
python manage.py migrate
python manage.py createcachetable
python manage.py seed_inventory

### 6. Create superuser
python manage.py createsuperuser

### 7. Run server
python manage.py runserver

## Tests
python manage.py test apps --settings=config.settings.test

Uses in-memory SQLite, so no database permissions are needed.

## Inventory integrity
python manage.py reconcile_inventory            # read-only report, exit 1 on discrepancies

See ../DEPLOYMENT.md for repair options, backups and production deployment.

## API Docs (DEBUG or ENABLE_API_DOCS=True, authentication required)
- /api/docs/
- /api/schema/

## Important Endpoints

### Auth
- POST /api/auth/login/  (returns {access}; sets the httpOnly refresh cookie)
- POST /api/auth/refresh/  (JSON body {}; uses and rotates the cookie)
- POST /api/auth/logout/  (JSON body {}; revokes the session and clears the cookie)
- GET /api/auth/me/

### Users
- GET /api/users/
- POST /api/users/

### Production
- GET /api/production/entries/
- POST /api/production/entries/
- POST /api/production/entries/{id}/void/  (admin; body: {"reason": "..."})

### Suppliers
- GET /api/suppliers/
- POST /api/suppliers/
- GET /api/suppliers/deliveries/
- POST /api/suppliers/deliveries/
- POST /api/suppliers/deliveries/{id}/void/  (admin; body: {"reason": "..."})

### Inventory
- GET /api/inventory/items/
- GET /api/inventory/balances/
- GET /api/inventory/transactions/
- POST /api/inventory/adjustments/  (admin; stock-count correction with reason)
- GET /api/inventory/reconciliation/  (admin; integrity report)

### Analytics
- GET /api/analytics/config/  (thresholds, windows, limits, periods, refresh cadence)
- GET /api/analytics/dashboard/
- GET /api/analytics/summary/?period=daily  (includes previous-period comparison)
- GET /api/analytics/trends/?start_date=&end_date=  (all series + anomaly flags; default last 30 days)
- GET /api/analytics/yield-trend/
- GET /api/analytics/inflow-vs-output/
- GET /api/analytics/downtime-trend/
- GET /api/analytics/reports/export/csv/?period=weekly
- GET /api/analytics/reports/export/pdf/?period=monthly