# 🏃‍♂️ Step Challenges App

A Django web application that allows teams and participants to compete in step-count challenges. Participants log their **total steps so far**, and the app provides live leaderboards, progress tracking, and recent activity.

Built as a friendly, lightweight challenge platform with a clean UI and simple data model.

---

## ✨ Features

- ✅ Create and manage step challenges
- 👥 Participants join teams within a challenge
- 📈 Participants log **cumulative step totals**
- 🏆 Mini leaderboards:
  - Top teams
  - Top participants
- ⏱ Challenge progress tracking (days elapsed / remaining)
- 🧠 Smart aggregation logic:
  - Uses each participant's **latest total_steps** entry
  - Team totals are computed as the **sum of latest steps of all team members**
- 🧪 Automated tests for critical edge cases
- 🎨 Responsive, card-based UI


---

## 🧱 Tech Stack

- **Backend**: Python, Django
- **Frontend**: Python, Django Templates + Bulma CSS
- **Database**: SQLite (locally), PostgreSQL
- **Auth**: Django authentication system

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/elliecdev/step_challenges.git
cd step_challenges
```

---

### 2️⃣ Create and activate a virtual environment

    python -m venv venv
    source venv/bin/activate  # macOS / Linux
    venv\Scripts\activate     # Windows

---

### 3️⃣ Install dependencies

    pip install -r requirements.txt

---

### 4️⃣ Run migrations

    python manage.py migrate

---

### 5️⃣ Create a superuser

    python manage.py createsuperuser

---

### 6️⃣ Start the development server

    python manage.py runserver

Visit:
- App: http://localhost:8000/
- Admin: http://localhost:8000/admin/

---

## 🧪 Running Tests

Run all tests for the `steps` app:

    python manage.py test steps

Tests include:
- **Models**: StepChallenge, Team, Participant, StepEntry (creation, `__str__`, StepEntry validation: date in range, no decreasing steps, closed challenge)
- **Views**: Home (participant lookup, no active challenge, quick stats), Login, StepEntry create/list (auth, permission), Leaderboard (anonymous + with challenge), `get_challenge_days` helper
- **Forms**: BulmaLoginForm, StepEntryForm, TeamAdminForm
- **Templatetags**: `add_class`, `nav_active`
- **URLs**: resolution for all named routes

---

## 📊 Test Coverage

Install dependencies (includes `coverage`):

    pip install -r requirements.txt

Run tests with coverage:

    coverage run --source=steps,challenges manage.py test steps

View a terminal report:

    coverage report

Generate an HTML report (opens in browser to explore line-by-line):

    coverage html
    open htmlcov/index.html   # macOS
    # or open htmlcov/index.html in your browser

Configuration is in `.coveragerc` (omits migrations, test files, and common no-cover lines).

---

## 📊 Step Entry Logic (Important)

Participants **log daily step counts** for each date in a challenge.

- Each `StepEntry` represents the **steps taken on that specific date** (`daily_steps`).
- **Participant leaderboard**: sums all of a participant’s `daily_steps` within a challenge.
- **Team leaderboard**: sums the total `daily_steps` of all participants assigned to the team.

This means all totals shown in the UI (home page status, quick stats, leaderboards) are based on the **sum of daily entries**, not a running cumulative counter.


---

## 🗂 Project Structure (Simplified)

    steps/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── tests/
    │   ├── test_models.py
    │   ├── test_views.py
    │   ├── test_home_view.py
    │   ├── test_forms.py
    │   ├── test_templatetags.py
    │   └── test_urls.py
    ├── templates/
    │   └── steps/
    │       └── home.html

---

## Data Model

### Relationship Diagram (Textual)
    StepChallenge
    ├── 1:N Teams
    │      └── 1:N Participants
    │                      |
    └──1:N StepEntries     └── 1:N StepEntries



### 🖼 Visual Data Model (Mermaid)

User is Django's built-in auth_user table

```mermaid
erDiagram
    USER ||--o{ PARTICIPANT : "1 user → many participants"
    PARTICIPANT ||--o{ STEPENTRY : "1 participant → many step entries"
    PARTICIPANT }o--|| TEAM : "many participants → 1 team"
    TEAM }o--|| STEPCHALLENGE : "many teams → 1 challenge"
    STEPCHALLENGE ||--o{ STEPENTRY : "1 challenge → many step entries"

    USER {
        int id PK
        varchar username
        varchar password
        varchar email
        varchar first_name
        varchar last_name
        boolean is_superuser
        boolean is_staff
        boolean is_active
        datetime date_joined
    }

    STEPCHALLENGE {
        int id PK
        varchar name
        date start_date
        date end_date
        boolean is_active
        datetime created_at
    }

    TEAM {
        int id PK
        varchar name
        varchar color
        int challenge_id FK
    }

    PARTICIPANT {
        int id PK
        int user_id FK
        int team_id FK
        datetime joined_at
    }

    STEPENTRY {
        int id PK
        int participant_id FK
        int challenge_id FK
        date date
        int daily_steps
        datetime created_at
    }
```

## Importing Historical Step Challenge Data

The project includes an ETL (Extract, Transform, Load) management command to import step challenge data from a CSV file.

### CSV File Format

The CSV file should have the following columns:
- **Date** - Entry date (format: `YYYY-MM-DD`)
- **Teams** - Team name (e.g., "Orange Team", "Red Team")
- **Member** - Participant name (format: "FirstName LastName")
- **Steps** - Daily step count (numbers, commas allowed)
- **Notes** - Optional notes (ignored during import)

Example:
```
Date,Teams,Member,Steps,Notes
2025-12-01,Orange Team,Jane Smith,4468,
2025-12-01,Red Team,John Doe,18138,
```

### Running the Import

```bash
python manage.py import_step_challenge /path/to/your/file.csv
```

### What the Import Does

The command performs four main steps:

1. **Creates Challenge** - Creates a new inactive step challenge
   - Name: "December 2025"
   - Start/End dates: Extracted from CSV data
   - Status: `is_active=False`

2. **Creates Teams** - Extracts unique team names from the CSV
   - Team names are extracted from the "Teams" column
   - Colors are automatically mapped based on team name (Orange→#FFA500, Red→#FF0000, etc.)
   - Creates or reuses existing teams

3. **Creates Participants** - Generates user accounts and participant records
   - Parses "FirstName LastName" format from the Member column
   - Creates usernames as `firstname.lastname` (lowercase, no spaces)
   - No password is set; users must reset their password to log in
   - Assigns each participant to their team

4. **Creates Step Entries** - Imports daily step counts
   - Parses dates in `YYYY-MM-DD` format
   - Converts step counts (handles commas in numbers)
   - Gracefully skips rows with missing data
   - Uses batch operations for efficiency

### Import Behavior

- **Idempotent**: Safe to run multiple times; won't create duplicates
- **Resilient**: Skips invalid or missing data and reports warnings
- **Efficient**: Uses `bulk_create()` for fast database operations
- **Historical Data**: Bypasses model validation to allow closed-challenge entries

### Example Output

```
Starting ETL process...
✓ Challenge created: December 2025
✓ 6 teams created
  Created: Orange Team (#FFA500)
  Created: Red Team (#FF0000)
  ...
✓ 24 participants created
  Created: jane.smith (Orange Team)
  Created: john.doe (Red Team)
  ...
✓ 508 step entries created
  Created: 508 entries
  Skipped: 236 entries
✓ ETL process completed successfully!
```

### Supported Team Colors

The script includes built-in color mappings for common team names:
- Orange Team → `#FFA500`
- Red Team → `#FF0000`
- Blue Team → `#0000FF`
- Green Team → `#008000`
- Yellow Team → `#FFFF00`
- Brown Team → `#8B4513`

To add additional team colors, edit the `COLOR_MAP` dictionary in `steps/management/commands/import_step_challenge.py`.

### Notes

- Users created during import have **no usable password** set
- Users must complete a password reset to log in
- Historical data is imported with `is_active=False` to prevent validation errors on closed challenges

## 🧭 Roadmap / Ideas

- ⏳ Historical progress charts
- 🏅 Badges & achievements
- 🌍 Internationalization (EN / FR)
- 📱 Mobile-first UI refinements

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Add tests for new behavior
4. Open a pull request

---

## 📄 License

This project is provided for learning and internal use.

---

## 🙌 Acknowledgements

Built with Django, focusing on:
- Correct data modeling
- Clear business logic
- Long-term maintainability
