from models import db
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret12222'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)
bcrypt = Bcrypt(app)

from models import User, RawMaterial, Production, Dispatch, Packaging, Filling


# 🔁 Create database
with app.app_context():
    db.create_all()

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# 1️⃣ Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/raw-intake')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# 2️⃣ Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=request.form['username'], password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    return render_template('register.html')

# 3️⃣ Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

# 4️⃣ Raw Material Intake
@app.route('/raw-intake', methods=['GET', 'POST'])
def raw_intake():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        raw = RawMaterial(
            name=request.form['name'],
            supplier=request.form['supplier'],
            city=request.form['city'],
            quantity=float(request.form['quantity']),
            unit=request.form['unit'],
            arrival=datetime.strptime(request.form['arrival'], '%Y-%m-%d'),
            receiver=request.form['receiver']
        )
        db.session.add(raw)
        db.session.commit()
        return redirect('/raw-intake')
    materials = RawMaterial.query.all()
    return render_template('raw_intake.html', materials=materials, now=datetime.now())

# 5️⃣ Production Entry
@app.route('/add-production', methods=['GET', 'POST'])
def add_production():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        production = Production(
            product=request.form['product'],
            batch_no=request.form['batch_no'],
            raw_material_id=request.form['raw_material_id'],
            issued_qty=round(float(request.form['issued_qty']), 5),
            used_qty=round(float(request.form['used_qty']), 5),
            unit=request.form['unit'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d')
        )
        db.session.add(production)
        db.session.commit()
        return redirect('/add-production')
    materials = RawMaterial.query.all()
    return render_template('production_entry.html', materials=materials, now=datetime.now())

# 6️⃣ Traceability Page
@app.route('/trace')
def trace():
    if 'user_id' not in session:
        return redirect('/')
    all_data = Production.query.all()
    trace_data = {}

    for p in all_data:
        if p.product not in trace_data:
            trace_data[p.product] = {
                'batch': p.batch_no,
                'issued': 0,
                'used': 0,
                'unit': p.unit,
                'materials': []
            }
        trace_data[p.product]['issued'] += p.issued_qty
        trace_data[p.product]['used'] += p.used_qty
        trace_data[p.product]['materials'].append(p)

    for item in trace_data.values():
        item['waste'] = round(item['issued'] - item['used'], 5)

    return render_template('trace.html', trace_data=trace_data, now=datetime.now())

# 7️⃣ Stock View
@app.route('/stock')
def stock():
    if 'user_id' not in session:
        return redirect('/')
    stock_data = RawMaterial.query.all()
    return render_template('stock.html', stock_data=stock_data, now=datetime.now())

# 8️⃣ Dispatch
@app.route('/dispatch', methods=['GET', 'POST'])
def dispatch():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        dispatch = Dispatch(
            supplier_batch_no=request.form['supplier_batch_no'],
            quantity=float(request.form['quantity']),
            frozen=(request.form['frozen'] == "Yes"),
            temperature=request.form['temperature'] if request.form['frozen'] == "Yes" else None,
            invoice=request.form['invoice'],
            box_no=request.form['box_no'],
            driver_phone=request.form['driver_phone'],
            vehicle_no=request.form['vehicle_no'],
            cleaning=(request.form.get('cleaning') == "Yes"),
            photo=None
        )
        photo_file = request.files['photo']
        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo_file.save(photo_path)
            dispatch.photo = filename

        db.session.add(dispatch)
        db.session.commit()
        return redirect('/dispatch')

    dispatches = Dispatch.query.all()
    return render_template('dispatch.html', dispatches=dispatches, now=datetime.now())


# Dispatch Table Page
@app.route('/dispatch-info')
def dispatch_info():
    if 'user_id' not in session:
        return redirect('/login')

    dispatches = Dispatch.query.all()
    return render_template('dispatch_info.html', dispatches=dispatches)

   
# 9️⃣ Packaging
@app.route('/packaging', methods=['GET', 'POST'])
def packaging():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        packaging = Packaging(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            brand=request.form['brand'],
            product=request.form['product'],
            product_batch_no=request.form['product_batch_no'],
            batch_no=request.form['batch_no'],
            expire_date=datetime.strptime(request.form['expire_date'], '%Y-%m-%d'),
            sealing=(request.form.get('sealing') == 'yes'),
            net_weight=float(request.form['net_weight']),
            observed_weight=float(request.form['observed_weight']),
            pallet=int(request.form['pallet']) if request.form.get('pallet') else 0,
            box=int(request.form['box']) if request.form.get('box') else 0,
            packets_per_box=int(request.form['packets_per_box']) if request.form.get('packets_per_box') else 0,
            tray=int(request.form['tray']) if request.form.get('tray') else 0,
            bottles_per_tray=int(request.form['bottles_per_tray']) if request.form.get('bottles_per_tray') else 0,
            checked_by=request.form['checked_by']
        )
        db.session.add(packaging)
        db.session.commit()
        return redirect('/packaging')

    packages = Packaging.query.all()
    return render_template('packaging.html', packages=packages, now=datetime.now())
@app.route('/packaging-detail')
def packaging_detail():
    if 'user_id' not in session:
        return redirect('/login')

    packages = Packaging.query.all()

    # Compute total weight for each package
    for p in packages:
        box_weight = p.box * p.packets_per_box * p.net_weight if p.box and p.packets_per_box else 0
        tray_weight = p.tray * p.bottles_per_tray * p.net_weight if p.tray and p.bottles_per_tray else 0
        p.total_weight = round(box_weight + tray_weight, 5)

    return render_template('packaging_detail.html', packages=packages, now=datetime.now())
# Fillings Form
@app.route('/fillings', methods=['GET', 'POST'])
def fillings():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        filling = Filling(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            product_name=request.form['product_name'],
            batch_no=request.form['batch_no'],
            container_type=request.form['container_type'],
            total_no=int(request.form['total_no']),
            net_weight=float(request.form['net_weight']),
            observed_weight=float(request.form['observed_weight']),
            brand=request.form['brand'],
            verified_by=request.form['verified_by']
        )
        db.session.add(filling)
        db.session.commit()
        return redirect('/fillings-sheet')
    

    return render_template('fillings.html')


# Fillings Sheet (with search)
@app.route('/fillings_sheet')
def fillings_sheet():
    search = request.args.get('search', '')
    if search:
        fillings = Filling.query.filter(
            (Filling.product_name.ilike(f'%{search}%')) |
            (Filling.batch_no.ilike(f'%{search}%')) |
            (Filling.brand.ilike(f'%{search}%'))
        ).all()
    else:
        fillings = Filling.query.all()

    return render_template('fillings_sheet.html', fillings=fillings, search=search)




# 🔟 Run the App
if __name__ == '__main__':
    app.run(debug=True)


