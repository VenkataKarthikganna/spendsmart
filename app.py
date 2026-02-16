from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

app.secret_key = "expense_secret_key"

# ✅ MySQL Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:karthik71316@localhost/expense_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ---------------- MODELS ---------------- #

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "❌ Username already exists!"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect("/")
        else:
            return "❌ Invalid Username or Password!"

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- DASHBOARD ---------------- #

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    expenses = Expense.query.filter_by(user_id=user_id).all()

    total = sum(exp.amount for exp in expenses)

    # ✅ Category Totals
    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0) + exp.amount

    # ✅ Monthly Totals
    monthly_totals = defaultdict(int)
    for exp in expenses:
        month = exp.date.strftime("%B")  # Example: January
        monthly_totals[month] += exp.amount

    return render_template(
        "index.html",
        username=session["username"],
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        monthly_totals=dict(monthly_totals)
    )


# ---------------- ADD EXPENSE ---------------- #

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        new_expense = Expense(
            user_id=session["user_id"],
            amount=amount,
            category=category,
            note=note
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect("/")

    return render_template("add_expense.html")


# ---------------- DELETE EXPENSE ---------------- #

@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    expense = Expense.query.get_or_404(id)

    if expense.user_id == session["user_id"]:
        db.session.delete(expense)
        db.session.commit()

    return redirect("/")


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
