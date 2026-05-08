# Library Service API

An online management system for book borrowings. Allows library administrators to manage books, users, borrowings, and payments through a RESTful API.

## Features

- **Books** — CRUD for books with inventory tracking (admin-only write access)
- **Users** — Registration and JWT authentication with custom `Authorize` header
- **Borrowings** — Borrow books with automatic inventory decrement; return with increment
- **Payments** — Stripe-powered checkout sessions for borrowings and overdue fines
- **Swagger UI** — Interactive API documentation at `/api/doc/`

## Tech Stack

- Python / Django / Django REST Framework
- PostgreSQL
- JWT authentication
- Stripe
- API docs
- Docker / Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose installed

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tetianasobko/library-service.git
   cd library-service
   ```

2. Copy the environment file and fill in your values:
   ```bash
   cp .env.sample .env
   ```

   Required variables in `.env`:
   ```
   SECRET_KEY=your_secret_key
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key

   POSTGRES_DB=your_library_db
   POSTGRES_USER=your_library_user
   POSTGRES_PASSWORD=your_library_password
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   PGDATA=/var/lib/postgresql/data
   ```

3. Build and run:
   ```bash
   docker-compose up --build
   ```

   The server will be available at `http://localhost:8000`.

### Running without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

## API Endpoints

### Users — `/api/users/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/users/` | Register a new user | No |
| POST | `/api/users/token/` | Obtain JWT tokens | No |
| POST | `/api/users/token/refresh/` | Refresh JWT token | No |
| GET | `/api/users/me/` | Get current user profile | Yes |
| PUT/PATCH | `/api/users/me/` | Update current user profile | Yes |

### Books — `/api/books/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/books/` | List all books | No |
| GET | `/api/books/<id>/` | Get book details | No |
| POST | `/api/books/` | Add a new book | Admin |
| PUT/PATCH | `/api/books/<id>/` | Update a book | Admin |
| DELETE | `/api/books/<id>/` | Delete a book | Admin |

### Borrowings — `/api/borrowings/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/borrowings/` | List borrowings | Yes |
| GET | `/api/borrowings/?is_active=true` | Filter active borrowings | Yes |
| GET | `/api/borrowings/?user_id=<id>` | Filter by user (admin only) | Admin |
| GET | `/api/borrowings/<id>/` | Get borrowing details | Yes |
| POST | `/api/borrowings/` | Create a borrowing | Yes |
| POST | `/api/borrowings/<id>/return/` | Return a borrowing | Yes |

### Payments — `/api/payments/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/payments/` | List payments | Yes |
| GET | `/api/payments/<id>/` | Get payment details | Yes |
| POST | `/api/payments/` | Create a Stripe payment session | Yes |

### API Docs

| Endpoint | Description |
|----------|-------------|
| `/api/doc/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI schema (JSON/YAML) |

## Authentication

The API uses JWT authentication with a custom header name `Authorize` (instead of the default `Authorization`) for easier use with the [ModHeader](https://modheader.com/) browser extension.

1. Obtain tokens via `POST /api/users/token/` with `email` and `password`.
2. Add the `Authorize: Bearer <access_token>` header to subsequent requests.

## Running Tests

```bash
python manage.py test
```
