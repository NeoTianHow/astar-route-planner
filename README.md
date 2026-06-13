# A* Route Planner

A Flask route-planning project that uses A* search over bus stop data and renders routes on an interactive map.

## Setup

1. Create and activate a virtual environment.

   ```powershell
   python -m venv env
   .\env\Scripts\activate
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your own rotated credentials.

4. Set the environment variables before running the app. PowerShell example:

   ```powershell
   $env:SECRET_KEY="replace-with-a-random-secret-key"
   ```

5. Run the app.

   ```powershell
   python start.py
   ```

## Admin Password Hash

Generate an admin password hash locally and store it in `ADMIN_PASSWORD_HASH`.

```powershell
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```
