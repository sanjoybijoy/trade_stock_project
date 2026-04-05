
# Django Project Update Workflow: Local → GitHub → PythonAnywhere


## 1️⃣ Local: Navigate to Project

```bash
# Go to your Django project directory
cd /path/to/your/django/project

# Check git status to see changed files
git status
```

---

## 2️⃣ Local: Stage and Commit Changes

```bash
# Stage all modified/new files
git add .

# Commit changes with a descriptive message
git commit -m "Describe your updates here"
```

---

## 3️⃣ Local: Push Changes to GitHub

```bash
# Check your current branch (usually main or master)
git branch

# Push changes to GitHub
git push origin main
```

> Replace `main` with your branch name if different.

---

## 4️⃣ PythonAnywhere: Pull Changes

```bash
# Open PythonAnywhere Bash console or SSH
# Navigate to your project folder
cd ~/yourproject

# Pull latest changes from GitHub
git pull origin main
```

---

## 5️⃣ PythonAnywhere: Apply Django Updates

```bash
# Install new dependencies if requirements.txt changed
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Reload your web app from PythonAnywhere Dashboard
```

---

## 6️⃣ Optional: Quick Local Push Command

```bash
# Stage, commit, and push in a single line
git add . && git commit -m "Your update message" && git push origin main
```

Then pull on PythonAnywhere as usual:

```bash
git pull origin main
```

