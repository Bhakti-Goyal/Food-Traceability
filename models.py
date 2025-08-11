from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class RawMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    supplier = db.Column(db.String(100))
    city = db.Column(db.String(100))
    quantity = db.Column(db.Float(precision=5))
    unit = db.Column(db.String(10))  # kg or l
    arrival = db.Column(db.Date)
    receiver = db.Column(db.String(100))

class Production(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100))
    batch_no = db.Column(db.String(100))
    raw_material_id = db.Column(db.Integer, db.ForeignKey('raw_material.id'))
    issued_qty = db.Column(db.Float(precision=5))
    used_qty = db.Column(db.Float(precision=5))
    unit = db.Column(db.String(10))  # kg or l
    date = db.Column(db.Date)
    raw_material = db.relationship('RawMaterial')

class Dispatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_batch_no = db.Column(db.String(100))
    quantity = db.Column(db.Float(precision=5))
    frozen = db.Column(db.Boolean)
    temperature = db.Column(db.String(10), nullable=True)
    invoice = db.Column(db.String(100))
    box_no = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    vehicle_no = db.Column(db.String(50))
    cleaning = db.Column(db.Boolean)
    photo = db.Column(db.String(200))

class Packaging(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    brand = db.Column(db.String(100))
    product = db.Column(db.String(100))
    product_batch_no = db.Column(db.String(100))
    batch_no = db.Column(db.String(100))
    expire_date = db.Column(db.Date)
    sealing = db.Column(db.Boolean)
    net_weight = db.Column(db.Float(precision=5))
    observed_weight = db.Column(db.Float(precision=5))
    pallet = db.Column(db.Integer, default=0)
    box = db.Column(db.Integer, default=0)
    packets_per_box = db.Column(db.Integer, default=0)
    tray = db.Column(db.Integer, default=0)
    bottles_per_tray = db.Column(db.Integer, default=0)
    checked_by = db.Column(db.String(100))

class Filling(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    batch_no = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'bottles' or 'packets'
    total_no = db.Column(db.Integer, nullable=False)
    net_weight = db.Column(db.Float, nullable=False)
    observed_weight = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    verified_by = db.Column(db.String(100), nullable=False)



    @property
    def total_weight(self):
        if self.box and self.packets_per_box:
            return round(self.box * self.packets_per_box * self.net_weight, 5)
        elif self.tray and self.bottles_per_tray:
            return round(self.tray * self.bottles_per_tray * self.net_weight, 5)
        else:
            return 0
