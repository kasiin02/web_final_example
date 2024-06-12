from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class DailyTransaction(db.Model):
    '''建立SQL資料庫的類型'''
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)  # 格式: yyMMdd
    class_ = db.Column(db.String, nullable=False)  # 'income' or 'expense'
    cost = db.Column(db.Float, nullable=False)
    category = db.Column(db.String)
    remark = db.Column(db.String)


@app.route('/delete_transaction', methods=['POST'])
def delete_transaction():
    '''刪除交易紀錄'''
    # 获取表单数据中的事务 ID
    transaction_id = request.form.get('transaction_id')
    print("xXXX")
    print(transaction_id)
    # 查询数据库以获取事务对象
    transaction = DailyTransaction.query.get(transaction_id)

    # 删除事务
    db.session.delete(transaction)
    db.session.commit()

    # 重定向到主页
    return redirect('/')


@app.route('/show_transaction', methods=['GET'])
def show_transaction():
    '''顯示收支圖表'''
    date_str = request.args.get('month')  # 20yy 或 20yyMM

    mT = []

    if len(date_str) == 4:  # Year
        year = date_str[2:]  # 取后两位，如'24'

        # 获取每年的收支情况
        year_incomes = db.session.query(
            DailyTransaction.category,
            func.sum(DailyTransaction.cost).label('total_income')
        ).filter(
            DailyTransaction.date.like(f'{year}%'),
            DailyTransaction.class_ == 'income'
        ).group_by(DailyTransaction.category).all()

        year_expenses = db.session.query(
            DailyTransaction.category,
            func.sum(DailyTransaction.cost).label('total_expense')
        ).filter(
            DailyTransaction.date.like(f'{year}%'),
            DailyTransaction.class_ == 'expense'
        ).group_by(DailyTransaction.category).all()

        income_details = [{'category': income.category if income.category else '其他', 'amount': income.total_income} for income in year_incomes]
        expense_details = [{'category': expense.category if expense.category else '其他', 'amount': expense.total_expense} for expense in year_expenses]

        total_income = sum(income['amount'] for income in income_details)
        total_expense = sum(expense['amount'] for expense in expense_details)

        balance = total_income - total_expense
        mT.append({
            'date': date_str,
            'income_details': income_details,
            'expense_details': expense_details,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance  # 添加余额
        })

    elif len(date_str) == 6:  # Month
        year = date_str[2:4]  # 取年
        month = date_str[4:]  # 取月

        # 获取每月的收支情况
        month_incomes = db.session.query(
            DailyTransaction.category,
            func.sum(DailyTransaction.cost).label('total_income')
        ).filter(
            DailyTransaction.date.like(f'{year}{month}%'),
            DailyTransaction.class_ == 'income'
        ).group_by(DailyTransaction.category).all()

        month_expenses = db.session.query(
            DailyTransaction.category,
            func.sum(DailyTransaction.cost).label('total_expense')
        ).filter(
            DailyTransaction.date.like(f'{year}{month}%'),
            DailyTransaction.class_ == 'expense'
        ).group_by(DailyTransaction.category).all()

        income_details = [{'category': income.category if income.category else '其他', 'amount': income.total_income} for income in month_incomes]
        expense_details = [{'category': expense.category if expense.category else '其他', 'amount': expense.total_expense} for expense in month_expenses]

        total_income = sum(income['amount'] for income in income_details)
        total_expense = sum(expense['amount'] for expense in expense_details)

        balance = total_income - total_expense
        mT.append({
            'date': date_str,
            'income_details': income_details,
            'expense_details': expense_details,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance  # 添加余额
        })

    return render_template('month.html', mT=mT)


with app.app_context():
    '''建立SQL'''
    db.create_all()


# 定義轉換 class 的函數
def translate_class(class_):
    '''英轉中'''
    if class_ == 'income':
        return '收入'
    elif class_ == 'expense':
        return '支出'
    else:
        return '未知'


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    '''新增交易紀錄'''
    if request.is_json:  # 判斷資料格式選用不同載入方法
        data = request.json
    else:
        data = request.form
    date_str = datetime.now().strftime('%y%m%d')  # 記錄當下的日期
    class_ = data['class']
    cost = float(data['cost'])
    category = data.get('category', '')
    remark = data.get('remark', '')

    new_transaction = DailyTransaction(
        date=date_str,
        class_=class_,
        cost=cost,
        category=category,
        remark=remark
    )

    db.session.add(new_transaction)
    db.session.commit()  # 更新資料庫

    if request.is_json:
        return jsonify({'message': 'Transaction added successfully'}), 201
    else:
        return redirect(url_for('index'))


def get_unique_years(transactions):
    '''生成年份清單'''
    years = set()
    for transaction in transactions:
        year = transaction.date[:2]  # 假设date格式为yyMMdd
        years.add(f"20{year}")
    return sorted(years)


def get_unique_months(transactions):
    '''生成月份清單'''
    months = set()
    for transaction in transactions:
        year = transaction.date[:2]  # 假设date格式为yyMMdd
        month = transaction.date[2:4]
        months.add(f"20{year}{month}")
    return sorted(months)


@app.route('/')
def index():
    '''首頁'''
    transactions = DailyTransaction.query.all()

    years = get_unique_years(transactions)
    months = get_unique_months(transactions)
    current_month = datetime.now().strftime('%Y%m')

    return render_template('index.html', transactions=transactions, years=years, months=months, current_month=current_month, translate_class=translate_class)


@app.route('/new_transaction')
def new_transaction():
    '''新增交易頁面'''
    return render_template('income.html')


@app.route('/edit/<int:transaction_id>')
def edit_transaction(transaction_id):
    transaction = DailyTransaction.query.get(transaction_id)
    if transaction:
        return render_template('edit.html', transaction=transaction)
    else:
        return "Transaction not found", 404


@app.route('/update_transaction', methods=['POST'])
def update_transaction():
    '''更新交易紀錄'''
    # 從表單中獲取要更新的交易 ID 和相關數據
    transaction_id = request.form.get('transaction_id')
    new_date = request.form.get('date')
    new_class = request.form.get('class')
    new_cost = request.form.get('cost')
    new_category = request.form.get('category')
    new_remark = request.form.get('remark')

    # 根據交易 ID 從資料庫中查找相應的交易記錄
    transaction = DailyTransaction.query.get(transaction_id)
    if not transaction:
        return "找不到相應的交易記錄", 404

    # 更新交易記錄的相關字段
    transaction.date = new_date
    transaction.class_ = new_class
    transaction.cost = new_cost
    transaction.category = new_category
    transaction.remark = new_remark

    # 將更新後的數據保存到資料庫中
    db.session.commit()

    # 重定向到主畫面
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
