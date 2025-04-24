from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
import random
from models import db, User, Vehicle, FuelRecord, MaintenanceRecord
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_wtf import CSRFProtect
from filters import translate_vehicle_type

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

# Добавляем фильтр в Jinja2
app.jinja_env.filters['translate_vehicle_type'] = translate_vehicle_type

# Настройка базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'fleet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)

def generate_test_vehicles():
    brands = {
        'car': ['Toyota', 'Honda', 'Volkswagen', 'Ford', 'Chevrolet', 'Nissan', 'Hyundai', 'Kia', 'Mazda', 'Subaru'],
        'truck': ['Volvo', 'Scania', 'MAN', 'Mercedes-Benz', 'Iveco', 'DAF', 'Renault', 'Kamaz', 'MAZ', 'Ural'],
        'van': ['Mercedes-Benz', 'Ford', 'Volkswagen', 'Fiat', 'Peugeot', 'Citroen', 'Renault', 'Iveco', 'Toyota', 'Nissan'],
        'bus': ['Mercedes-Benz', 'Volvo', 'Scania', 'MAN', 'Iveco', 'Neoplan', 'Setra', 'Yutong', 'Higer', 'King Long'],
        'suv': ['Toyota', 'Honda', 'Nissan', 'Mitsubishi', 'Jeep', 'Land Rover', 'BMW', 'Mercedes-Benz', 'Audi', 'Volvo'],
        'minivan': ['Toyota', 'Honda', 'Nissan', 'Kia', 'Hyundai', 'Chrysler', 'Ford', 'Mercedes-Benz', 'Volkswagen', 'Peugeot'],
        'pickup': ['Ford', 'Toyota', 'Chevrolet', 'Nissan', 'GMC', 'Ram', 'Mitsubishi', 'Isuzu', 'Mazda', 'Great Wall'],
        'special': ['Caterpillar', 'Komatsu', 'Hitachi', 'Volvo', 'Liebherr', 'JCB', 'Doosan', 'Hyundai', 'Sany', 'XCMG'],
        'excavator': ['Caterpillar', 'Komatsu', 'Hitachi', 'Volvo', 'Liebherr', 'JCB', 'Doosan', 'Hyundai', 'Sany', 'XCMG'],
        'bulldozer': ['Caterpillar', 'Komatsu', 'Hitachi', 'Volvo', 'Liebherr', 'JCB', 'Doosan', 'Hyundai', 'Sany', 'XCMG'],
        'crane': ['Liebherr', 'Tadano', 'Grove', 'Terex', 'Manitowoc', 'Kobelco', 'XCMG', 'Sany', 'Zoomlion', 'Hitachi'],
        'trailer': ['Schmitz', 'Krone', 'Kogel', 'Lamberet', 'Chereau', 'Wielton', 'Krone', 'Schwarzmuller', 'Tirsan', 'Kassbohrer'],
        'motorcycle': ['Honda', 'Yamaha', 'Suzuki', 'Kawasaki', 'Harley-Davidson', 'BMW', 'Ducati', 'KTM', 'Triumph', 'Aprilia']
    }

    models = {
        'car': ['Camry', 'Corolla', 'Civic', 'Accord', 'Golf', 'Passat', 'Focus', 'Fusion', 'Cruze', 'Malibu'],
        'truck': ['FH16', 'R-Series', 'TGX', 'Actros', 'Stralis', 'XF', 'T-Series', 'Truck', 'Truck', 'Truck'],
        'van': ['Sprinter', 'Transit', 'Crafter', 'Ducato', 'Boxer', 'Jumper', 'Master', 'Daily', 'Hiace', 'NV400'],
        'bus': ['Citaro', '9700', 'Tourismo', 'Lion\'s Coach', 'Evadys', 'Setra', 'Tourliner', 'ZK6122', 'A50', 'XMQ6129'],
        'suv': ['RAV4', 'CR-V', 'Rogue', 'Outlander', 'Wrangler', 'Range Rover', 'X5', 'GLE', 'Q7', 'XC90'],
        'minivan': ['Sienna', 'Odyssey', 'Quest', 'Sedona', 'Carnival', 'Pacifica', 'Transit', 'V-Class', 'Multivan', 'Traveller'],
        'pickup': ['F-150', 'Tundra', 'Silverado', 'Titan', 'Sierra', '1500', 'L200', 'D-Max', 'BT-50', 'Wingle'],
        'special': ['D6', 'D65', 'ZX350', 'EC220', 'L 566', '3CX', 'DX225', 'R220LC', 'SY365', 'XE215'],
        'excavator': ['320', 'PC200', 'ZX350', 'EC220', 'L 566', '3CX', 'DX225', 'R220LC', 'SY365', 'XE215'],
        'bulldozer': ['D6', 'D65', 'D85', 'D155', 'D275', 'D355', 'D475', 'D575', 'D675', 'D775'],
        'crane': ['LTM 1200', 'ATF 220G', 'GMK 5250L', 'AC 500', 'Grove GMK 5250L', 'CKE 2500', 'QAY 500', 'SAC 2200', 'ZTC 2500', 'QUY 500'],
        'trailer': ['S.KO', 'S.CF', 'S.CS', 'S.KI', 'S.KO', 'S.CF', 'S.CS', 'S.KI', 'S.KO', 'S.CF'],
        'motorcycle': ['CBR1000RR', 'YZF-R1', 'GSX-R1000', 'Ninja ZX-10R', 'Sportster', 'S 1000 RR', 'Panigale', '1290 Super Duke', 'Speed Triple', 'RSV4']
    }

    def generate_plate():
        letters = 'АВЕКМНОРСТУХ'
        numbers = '0123456789'
        return f"{random.choice(letters)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(letters)}{random.choice(letters)}"

    def generate_vin():
        letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
        numbers = '0123456789'
        return ''.join(random.choice(letters + numbers) for _ in range(17))

    vehicles = []
    for _ in range(100):
        vehicle_type = random.choice(list(brands.keys()))
        brand = random.choice(brands[vehicle_type])
        model = random.choice(models[vehicle_type])
        name = f"{brand} {model}"
        
        vehicle = Vehicle(
            name=name,
            type=vehicle_type,
            plate=generate_plate(),
            status=random.choice(['active', 'active', 'active', 'active', 'maintenance']),  # 80% active, 20% maintenance
            mileage=random.randint(1000, 500000),
            brand=brand,
            vin=generate_vin(),
            year=random.randint(2000, 2024)
        )
        vehicles.append(vehicle)
    
    return vehicles

def create_sample_fuel_records():
    vehicles = Vehicle.query.all()
    if not FuelRecord.query.first():
        for vehicle in vehicles:
            # Определяем тип топлива в зависимости от типа транспортного средства
            if vehicle.type in ['car', 'suv', 'minivan', 'pickup']:
                fuel_type = random.choice(['АИ-95', 'АИ-98', 'АИ-92'])
            elif vehicle.type in ['truck', 'bus', 'van', 'special', 'excavator', 'bulldozer', 'crane', 'trailer']:
                fuel_type = 'ДТ'
            elif vehicle.type == 'motorcycle':
                fuel_type = random.choice(['АИ-95', 'АИ-98'])
            else:
                fuel_type = 'АИ-95'
            
            # Генерируем от 5 до 15 заправок для каждого транспортного средства
            num_records = random.randint(5, 15)
            current_mileage = vehicle.mileage
            current_date = datetime.now() - timedelta(days=random.randint(0, 365))
            
            for _ in range(num_records):
                # Генерируем реалистичные значения
                if fuel_type in ['АИ-95', 'АИ-98', 'АИ-92']:
                    fuel_quantity = round(random.uniform(30, 70), 1)  # 30-70 литров для легковых
                    fuel_cost = round(fuel_quantity * random.uniform(45, 55), 2)  # 45-55 руб/л
                else:  # ДТ
                    fuel_quantity = round(random.uniform(50, 200), 1)  # 50-200 литров для грузовых
                    fuel_cost = round(fuel_quantity * random.uniform(50, 60), 2)  # 50-60 руб/л
                
                # Увеличиваем пробег на 500-2000 км между заправками
                mileage_increase = random.randint(500, 2000)
                current_mileage += mileage_increase
                
                # Создаем запись о заправке
                fuel_record = FuelRecord(
                    vehicle_id=vehicle.id,
                    date=current_date,
                    fuel_quantity=fuel_quantity,
                    fuel_cost=fuel_cost,
                    mileage=current_mileage,
                    fuel_type=fuel_type
                )
                db.session.add(fuel_record)
                
                # Переходим к следующей дате (1-7 дней между заправками)
                current_date -= timedelta(days=random.randint(1, 7))
            
            db.session.commit()
            print("Тестовые записи о заправках успешно созданы")

def create_sample_maintenance_records():
    vehicles = Vehicle.query.all()
    if not MaintenanceRecord.query.first():
        for vehicle in vehicles:
            # Определяем тип обслуживания в зависимости от типа транспортного средства
            if vehicle.type in ['car', 'suv', 'minivan', 'pickup', 'motorcycle']:
                # Для легковых автомобилей и мотоциклов
                descriptions = [
                    'Замена масла и фильтров',
                    'Замена тормозных колодок',
                    'Замена ремня ГРМ',
                    'Диагностика ходовой части',
                    'Замена свечей зажигания',
                    'Проверка тормозной системы',
                    'Замена воздушного фильтра',
                    'Замена салонного фильтра',
                    'Проверка системы охлаждения',
                    'Замена топливного фильтра'
                ]
                costs = [5000, 8000, 15000, 3000, 4000, 2000, 1500, 2000, 2500, 3000]
                mileage_intervals = [10000, 30000, 60000, 15000, 30000, 20000, 15000, 15000, 20000, 30000]
            else:
                # Для грузовых автомобилей и спецтехники
                descriptions = [
                    'Замена масла и фильтров',
                    'Замена тормозных колодок',
                    'Замена ремня ГРМ',
                    'Диагностика ходовой части',
                    'Замена топливного фильтра',
                    'Проверка тормозной системы',
                    'Замена воздушного фильтра',
                    'Замена салонного фильтра',
                    'Проверка системы охлаждения',
                    'Замена масла в КПП'
                ]
                costs = [8000, 12000, 25000, 5000, 5000, 4000, 3000, 3000, 4000, 6000]
                mileage_intervals = [15000, 40000, 80000, 20000, 30000, 25000, 20000, 20000, 25000, 40000]
            
            # Генерируем от 3 до 8 записей ТО для каждого транспортного средства
            num_records = random.randint(3, 8)
            current_mileage = vehicle.mileage
            current_date = datetime.now() - timedelta(days=random.randint(0, 365))
            
            for _ in range(num_records):
                # Выбираем случайное обслуживание
                index = random.randint(0, len(descriptions) - 1)
                description = descriptions[index]
                cost = costs[index]
                mileage_interval = mileage_intervals[index]
                
                # Увеличиваем пробег на 5000-15000 км между обслуживаниями
                mileage_increase = random.randint(5000, 15000)
                current_mileage += mileage_increase
                
                # Создаем запись о ТО
                maintenance_record = MaintenanceRecord(
                    vehicle_id=vehicle.id,
                    date=current_date,
                    description=description,
                    mileage=current_mileage,
                    cost=cost,
                    next_maintenance_mileage=current_mileage + mileage_interval
                )
                db.session.add(maintenance_record)
                
                # Переходим к следующей дате (30-90 дней между обслуживаниями)
                current_date -= timedelta(days=random.randint(30, 90))
            
        db.session.commit()
        print("Тестовые записи о техническом обслуживании успешно созданы")

def create_inactive_vehicles():
    inactive_vehicles = [
        {
            'name': 'Toyota Camry',
            'type': 'car',
            'plate': 'А123АА777',
            'brand': 'Toyota',
            'vin': 'JT2BF22K1W0123456',
            'status': 'inactive',
            'year': '2018',
            'mileage': 150000
        },
        {
            'name': 'Volkswagen Passat',
            'type': 'car',
            'plate': 'В456ВВ777',
            'brand': 'Volkswagen',
            'vin': 'WVWZZZ3CZEE123456',
            'status': 'inactive',
            'year': '2019',
            'mileage': 120000
        },
        {
            'name': 'Ford Transit',
            'type': 'van',
            'plate': 'С789СС777',
            'brand': 'Ford',
            'vin': 'WF0EXXGBBE1234567',
            'status': 'inactive',
            'year': '2020',
            'mileage': 80000
        },
        {
            'name': 'Mercedes Sprinter',
            'type': 'van',
            'plate': 'Е012ЕЕ777',
            'brand': 'Mercedes',
            'vin': 'WDB9066331S123456',
            'status': 'inactive',
            'year': '2021',
            'mileage': 60000
        },
        {
            'name': 'Volvo FH16',
            'type': 'truck',
            'plate': 'К345КК777',
            'brand': 'Volvo',
            'vin': 'YV1LFA0ACB1234567',
            'status': 'inactive',
            'year': '2017',
            'mileage': 300000
        },
        {
            'name': 'Scania R450',
            'type': 'truck',
            'plate': 'М678ММ777',
            'brand': 'Scania',
            'vin': 'YS2K4X20001876543',
            'status': 'inactive',
            'year': '2018',
            'mileage': 250000
        },
        {
            'name': 'MAN TGX',
            'type': 'truck',
            'plate': 'Н901НН777',
            'brand': 'MAN',
            'vin': 'WMA06ZZZ9KZ123456',
            'status': 'inactive',
            'year': '2019',
            'mileage': 200000
        }
    ]

    for vehicle_data in inactive_vehicles:
        # Проверяем, существует ли уже транспортное средство с таким VIN
        existing_vehicle = Vehicle.query.filter_by(vin=vehicle_data['vin']).first()
        if not existing_vehicle:
            new_vehicle = Vehicle(**vehicle_data)
            db.session.add(new_vehicle)
    
    try:
        db.session.commit()
        print("Неактивные транспортные средства успешно добавлены")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при добавлении неактивных транспортных средств: {str(e)}")

def init_db():
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Создаем тестового администратора, если его нет
        if not User.query.filter_by(email='fleet_admin@example.com').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                role='admin',
                email='fleet_admin@example.com',
                phone='+79001234567'
            )
            db.session.add(admin)
            db.session.commit()
        
        # Создаем тестовые транспортные средства, если их нет
        if not Vehicle.query.first():
            vehicles = generate_test_vehicles()
            for vehicle in vehicles:
                db.session.add(vehicle)
            db.session.commit()
            print("Тестовые транспортные средства успешно созданы")
        
        # Добавляем неактивные транспортные средства
        create_inactive_vehicles()
        
        # Создаем тестовые записи о заправках
        create_sample_fuel_records()
        
        # Создаем тестовые записи о техническом обслуживании
        create_sample_maintenance_records()
        
        db.session.commit()

# Инициализируем базу данных при запуске
init_db()

@app.route('/')
@login_required
def index():
    # Получаем текущую дату
    current_date = datetime.now()
    
    # Получаем статистику по транспортным средствам
    total_vehicles = Vehicle.query.count()
    active_vehicles = Vehicle.query.filter_by(status='active').count()
    maintenance_vehicles = Vehicle.query.filter_by(status='maintenance').count()
    inactive_vehicles = Vehicle.query.filter_by(status='inactive').count()
    
    # Получаем статистику по заправкам за текущий месяц
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_fuelings = FuelRecord.query.filter(FuelRecord.date >= start_of_month).count()
    total_fuel_volume = db.session.query(db.func.sum(FuelRecord.fuel_quantity)).filter(FuelRecord.date >= start_of_month).scalar() or 0
    
    # Получаем статистику по обслуживанию
    total_maintenance = MaintenanceRecord.query.filter(MaintenanceRecord.date >= start_of_month).count()
    
    # Получаем общие расходы за текущий месяц
    total_expenses = (db.session.query(db.func.sum(FuelRecord.fuel_cost)).filter(FuelRecord.date >= start_of_month).scalar() or 0) + \
                    (db.session.query(db.func.sum(MaintenanceRecord.cost)).filter(MaintenanceRecord.date >= start_of_month).scalar() or 0)
    
    # Получаем последние записи
    recent_fuelings = FuelRecord.query.order_by(FuelRecord.date.desc()).limit(5).all()
    recent_maintenance = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).limit(5).all()
    
    return render_template('index.html',
                         total_vehicles=total_vehicles,
                         active_vehicles=active_vehicles,
                         maintenance_vehicles=maintenance_vehicles,
                         inactive_vehicles=inactive_vehicles,
                         total_fuelings=total_fuelings,
                         total_fuel_volume=total_fuel_volume,
                         total_maintenance=total_maintenance,
                         total_expenses=total_expenses,
                         recent_fuelings=recent_fuelings,
                         recent_maintenance=recent_maintenance,
                         current_date=current_date)

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('dashboard'))

    # Получаем все необходимые данные
    users = User.query.all()
    vehicles = Vehicle.query.all()
    maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).limit(5).all()
    fuel_records = FuelRecord.query.order_by(FuelRecord.date.desc()).limit(5).all()
    
    # Статистика
    total_vehicles = len(vehicles)
    active_vehicles = len([v for v in vehicles if v.status == 'active'])
    maintenance_vehicles = len([v for v in vehicles if v.status == 'maintenance'])
    total_users = len(users)
    
    return render_template('admin_panel.html', 
                         users=users,
                         vehicles=vehicles,
                         maintenance_records=maintenance_records,
                         fuel_records=fuel_records,
                         total_vehicles=total_vehicles,
                         active_vehicles=active_vehicles,
                         maintenance_vehicles=maintenance_vehicles,
                         total_users=total_users)

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('vehicles_list'))

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            name = request.form.get('name')
            type = request.form.get('type')
            plate = request.form.get('plate')
            brand = request.form.get('brand')
            vin = request.form.get('vin')
            status = request.form.get('status')
            year = request.form.get('year')
            mileage = request.form.get('mileage')

            # Проверяем наличие всех обязательных полей
            if not all([name, type, plate, brand, vin, status, year, mileage]):
                flash('Пожалуйста, заполните все обязательные поля', 'danger')
                return redirect(url_for('add_vehicle'))

            # Проверяем, существует ли уже транспортное средство с таким VIN
            existing_vehicle = Vehicle.query.filter_by(vin=vin).first()
            if existing_vehicle:
                flash('Транспортное средство с таким VIN уже существует', 'danger')
                return redirect(url_for('add_vehicle'))

            # Проверяем, существует ли уже транспортное средство с таким номером
            existing_plate = Vehicle.query.filter_by(plate=plate).first()
            if existing_plate:
                flash('Транспортное средство с таким номером уже существует', 'danger')
                return redirect(url_for('add_vehicle'))

            # Создаем новое транспортное средство
            new_vehicle = Vehicle(
                name=name,
                type=type,
                plate=plate,
                brand=brand,
                vin=vin,
                status=status,
                year=year,
                mileage=float(mileage)
            )

            db.session.add(new_vehicle)
            db.session.commit()
            flash('Транспортное средство успешно добавлено', 'success')
            return redirect(url_for('vehicles_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при добавлении транспортного средства: {str(e)}', 'danger')
            return redirect(url_for('add_vehicle'))

    return render_template('add_vehicle.html')

@app.route('/vehicles')
@login_required
def vehicles_list():
    # Получаем параметры поиска и фильтрации
    search_query = request.args.get('search', '')
    selected_type = request.args.get('type', '')
    selected_status = request.args.get('status', '')
    
    # Начинаем с базового запроса
    query = Vehicle.query
    
    # Применяем поиск, если указан
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Vehicle.name.ilike(search),
                Vehicle.plate.ilike(search),
                Vehicle.brand.ilike(search),
                Vehicle.vin.ilike(search)
            )
        )
    
    # Применяем фильтры по типу и статусу
    if selected_type:
        query = query.filter(Vehicle.type == selected_type)
    if selected_status:
        query = query.filter(Vehicle.status == selected_status)
    
    # Получаем отфильтрованный список транспортных средств
    vehicles = query.order_by(Vehicle.name).all()
    
    return render_template('vehicles_list.html', 
                         vehicles=vehicles,
                         selected_type=selected_type,
                         selected_status=selected_status,
                         search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['username'] = username
            session['role'] = user.role
            
            # Получаем URL для перенаправления
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Неверное имя пользователя или пароль', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/manager')
def manager_panel():
    if 'username' not in session or session.get('role') != 'manager':
        flash('Доступ запрещен. Требуются права менеджера.', 'danger')
        return redirect(url_for('index'))
    
    vehicles = Vehicle.query.all()
    maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.date.desc()).limit(5).all()
    fuel_records = FuelRecord.query.order_by(FuelRecord.date.desc()).limit(5).all()
    
    return render_template('manager_panel.html', 
                         vehicles=vehicles,
                         maintenance_records=maintenance_records,
                         fuel_records=fuel_records)

@app.route('/maintenance')
@login_required
def maintenance():
    # Получаем параметры фильтрации
    vehicle_id = request.args.get('vehicle')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Начинаем с базового запроса
    query = MaintenanceRecord.query
    
    # Применяем фильтры
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    if start_date:
        query = query.filter(MaintenanceRecord.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(MaintenanceRecord.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    # Получаем отфильтрованные записи
    records = query.order_by(MaintenanceRecord.date.desc()).all()
    
    # Рассчитываем статистику
    total_records = len(records)
    total_cost = sum(record.cost for record in records)
    maintenance_vehicles = len(set(record.vehicle_id for record in records))
    avg_cost = total_cost / total_records if total_records > 0 else 0
    
    # Получаем все транспортные средства для выпадающего списка
    vehicles = Vehicle.query.all()
    
    return render_template('maintenance.html',
                         records=records,
                         vehicles=vehicles,
                         total_records=total_records,
                         total_cost=total_cost,
                         maintenance_vehicles=maintenance_vehicles,
                         avg_cost=avg_cost,
                         selected_vehicle=vehicle_id,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/add_fuel', methods=['GET', 'POST'])
@login_required
def add_fuel():
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('fuel'))
    
    vehicles = Vehicle.query.all()

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            vehicle_id = request.form.get('vehicle')
            date = request.form.get('date')
            fuel_type = request.form.get('fuel_type')
            fuel_quantity = request.form.get('fuel_quantity')
            fuel_cost = request.form.get('fuel_cost')
            mileage = request.form.get('mileage')
            notes = request.form.get('notes')
            
            # Проверяем наличие всех необходимых данных
            if not all([vehicle_id, date, fuel_type, fuel_quantity, fuel_cost, mileage]):
                flash('Пожалуйста, заполните все обязательные поля', 'danger')
                return redirect(url_for('add_fuel'))
            
            # Получаем транспортное средство для проверки типа топлива
            vehicle = Vehicle.query.get(vehicle_id)
            if not vehicle:
                flash('Транспортное средство не найдено', 'danger')
                return redirect(url_for('add_fuel'))
            
            # Проверяем корректность типа топлива для данного транспортного средства
            if vehicle.type in ['truck', 'bus', 'van', 'special', 'excavator', 'bulldozer', 'crane', 'trailer']:
                if fuel_type != 'ДТ':
                    flash('Для данного типа транспортного средства разрешено только дизельное топливо (ДТ)', 'danger')
                    return redirect(url_for('add_fuel'))
            
            # Создаем новую запись о заправке
            new_fuel = FuelRecord(
                vehicle_id=vehicle_id,
                date=datetime.strptime(date, '%Y-%m-%d'),
                fuel_type=fuel_type,
                fuel_quantity=float(fuel_quantity),
                fuel_cost=float(fuel_cost),
                mileage=float(mileage),
                notes=notes
            )
            
            db.session.add(new_fuel)
            db.session.commit()
            flash('Запись о заправке успешно добавлена', 'success')
            return redirect(url_for('fuel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при добавлении записи: {str(e)}', 'danger')
            return redirect(url_for('add_fuel'))

    return render_template('add_fuel.html', 
                         vehicles=vehicles,
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/fuel')
@login_required
def fuel():
    # Получаем параметры фильтрации
    vehicle_id = request.args.get('vehicle')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Начинаем с базового запроса
    query = FuelRecord.query
    
    # Применяем фильтры
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    if start_date:
        query = query.filter(FuelRecord.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(FuelRecord.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    # Получаем отфильтрованные записи
    records = query.order_by(FuelRecord.date.desc()).all()
    
    # Рассчитываем статистику
    total_records = len(records)
    total_cost = sum(record.fuel_cost for record in records)
    total_fuel = sum(record.fuel_quantity for record in records)
    avg_cost = total_cost / total_records if total_records > 0 else 0
    
    # Получаем все транспортные средства для выпадающего списка
    vehicles = Vehicle.query.all()
    
    return render_template('fuel.html',
                         records=records,
                         vehicles=vehicles,
                         total_records=total_records,
                         total_cost=total_cost,
                         total_fuel=total_fuel,
                         avg_cost=avg_cost,
                         selected_vehicle=vehicle_id,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/api/maintenance_data')
def maintenance_data():
    return jsonify({
        "data": [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 2
        ],
        "labels": [
            "2025-03-26", "2025-03-27", "2025-03-28", "2025-03-29", "2025-03-30",
            "2025-03-31", "2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04",
            "2025-04-05", "2025-04-06", "2025-04-07", "2025-04-08", "2025-04-09",
            "2025-04-10", "2025-04-11", "2025-04-12", "2025-04-13", "2025-04-14",
            "2025-04-15", "2025-04-16", "2025-04-17", "2025-04-18", "2025-04-19",
            "2025-04-20", "2025-04-21", "2025-04-22", "2025-04-23", "2025-04-24"
        ],
        "title": "Количество технических обслуживаний за последние 30 дней"
    })

@app.route('/api/fuel_data')
def fuel_data():
    return jsonify({
        "data": [
            1004.77, 649.91, 546.95, 1131.53, 1481.37,
            551.7, 863.87, 933.14, 593.43, 785.37
        ],
        "labels": [
            "2025-04-15", "2025-04-16", "2025-04-17", "2025-04-18", "2025-04-19",
            "2025-04-20", "2025-04-21", "2025-04-22", "2025-04-23", "2025-04-24"
        ]
    })

@app.route('/add_maintenance', methods=['GET', 'POST'])
def add_maintenance():
    if 'username' not in session or (session.get('role') != 'admin' and session.get('role') != 'manager'):
        flash('Доступ запрещен. Требуются права администратора или менеджера.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        vehicle_id = int(request.form['vehicle_id'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form['description']
        mileage = float(request.form['mileage'])
        cost = float(request.form.get('cost', 0))
        next_maintenance_mileage = float(request.form.get('next_maintenance_mileage', 0))

        maintenance_record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=date,
            description=description,
            mileage=mileage,
            cost=cost,
            next_maintenance_mileage=next_maintenance_mileage
        )
        db.session.add(maintenance_record)
        db.session.commit()

        return redirect(url_for('maintenance'))

    vehicles = Vehicle.query.all()
    return render_template('add_maintenance.html', vehicles=vehicles)

@app.route('/vehicle/<int:vehicle_id>')
def vehicle_details(vehicle_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    maintenance_records = MaintenanceRecord.query.filter_by(vehicle_id=vehicle_id).order_by(MaintenanceRecord.date.desc()).all()
    fuel_records = FuelRecord.query.filter_by(vehicle_id=vehicle_id).order_by(FuelRecord.date.desc()).all()
    
    return render_template('vehicle_details.html', 
                         vehicle=vehicle,
                         maintenance_records=maintenance_records,
                         fuel_records=fuel_records)

@app.route('/edit_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('vehicles_list'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            vehicle.name = request.form.get('name')
            vehicle.type = request.form.get('type')
            vehicle.plate = request.form.get('plate')
            vehicle.brand = request.form.get('brand')
            vehicle.vin = request.form.get('vin')
            vehicle.status = request.form.get('status')
            vehicle.year = request.form.get('year')
            vehicle.mileage = float(request.form.get('mileage', 0))

            # Проверяем наличие всех обязательных полей
            if not all([vehicle.name, vehicle.type, vehicle.plate, vehicle.brand, vehicle.vin, vehicle.status]):
                flash('Пожалуйста, заполните все обязательные поля', 'danger')
                return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))

            # Проверяем, существует ли уже транспортное средство с таким VIN
            existing_vehicle = Vehicle.query.filter(Vehicle.vin == vehicle.vin, Vehicle.id != vehicle_id).first()
            if existing_vehicle:
                flash('Транспортное средство с таким VIN уже существует', 'danger')
                return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))

            # Проверяем, существует ли уже транспортное средство с таким номером
            existing_plate = Vehicle.query.filter(Vehicle.plate == vehicle.plate, Vehicle.id != vehicle_id).first()
            if existing_plate:
                flash('Транспортное средство с таким номером уже существует', 'danger')
                return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))

            # Сохраняем изменения
            db.session.commit()
            flash('Транспортное средство успешно обновлено', 'success')
            return redirect(url_for('vehicles_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при обновлении транспортного средства: {str(e)}', 'danger')
            return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))
    
    return render_template('edit_vehicle.html', vehicle=vehicle)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        email = request.form.get('email')
        phone = request.form.get('phone')

        if not email:
            flash('Email является обязательным полем', 'danger')
            return redirect(url_for('add_user'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('add_user'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('add_user'))

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role=role,
            email=email,
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Пользователь успешно добавлен', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('add_user.html')

@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('edit_user', id=id))

        user.username = username
        user.role = role
        if password:
            user.password = generate_password_hash(password)
        
        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    
    if user.username == session['username']:
        flash('Нельзя удалить текущего пользователя', 'danger')
        return redirect(url_for('admin_panel'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/delete_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def delete_vehicle(vehicle_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен. Требуются права администратора.', 'danger')
        return redirect(url_for('vehicles_list'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Удаляем связанные записи
    MaintenanceRecord.query.filter_by(vehicle_id=vehicle_id).delete()
    FuelRecord.query.filter_by(vehicle_id=vehicle_id).delete()
    
    # Удаляем транспортное средство
    db.session.delete(vehicle)
    db.session.commit()
    
    flash('Транспортное средство успешно удалено', 'success')
    return redirect(url_for('vehicles_list'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # Проверка существования пользователя
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))
        
        # Проверка совпадения паролей
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        # Создание нового пользователя
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role='user',
            email=email,
            phone=phone
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешно завершена. Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/edit_maintenance/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_maintenance(id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('maintenance'))
    
    record = MaintenanceRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Проверяем CSRF-токен
            if not request.form.get('csrf_token'):
                flash('Ошибка безопасности. Пожалуйста, попробуйте снова.', 'danger')
                return redirect(url_for('edit_maintenance', id=id))
            
            # Обновляем данные
            record.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
            record.description = request.form.get('description')
            record.mileage = float(request.form.get('mileage'))
            record.cost = float(request.form.get('cost'))
            record.next_maintenance_mileage = float(request.form.get('next_maintenance_mileage', 0))
            
            db.session.commit()
            flash('Запись о техническом обслуживании успешно обновлена', 'success')
            return redirect(url_for('maintenance'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при обновлении записи: {str(e)}', 'danger')
            return redirect(url_for('edit_maintenance', id=id))
    
    return render_template('edit_maintenance.html', record=record)

@app.route('/add_fuel_bulk', methods=['GET', 'POST'])
@login_required
def add_fuel_bulk():
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('fuel'))
    
    vehicles = Vehicle.query.all()
    
    if request.method == 'POST':
        try:
            date = request.form.get('date')
            if not date:
                flash('Пожалуйста, укажите дату заправки', 'danger')
                return redirect(url_for('add_fuel_bulk'))
            
            for vehicle in vehicles:
                fuel_quantity = request.form.get(f'fuel_quantity_{vehicle.id}')
                cost = request.form.get(f'cost_{vehicle.id}')
                mileage = request.form.get(f'mileage_{vehicle.id}')
                
                # Пропускаем пустые записи
                if not (fuel_quantity and cost and mileage):
                    continue
                
                new_fuel = FuelRecord(
                    vehicle_id=vehicle.id,
                    date=date,
                    fuel_quantity=float(fuel_quantity),
                    fuel_cost=float(cost),
                    mileage=float(mileage)
                )
                db.session.add(new_fuel)
            
            db.session.commit()
            flash('Записи о заправках успешно добавлены', 'success')
            return redirect(url_for('fuel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при добавлении записей: {str(e)}', 'danger')
            return redirect(url_for('add_fuel_bulk'))
    
    return render_template('add_fuel_bulk.html', vehicles=vehicles)

@app.route('/edit_fuel/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_fuel(id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('fuel'))
    
    record = FuelRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            date = request.form.get('date')
            fuel_quantity = request.form.get('fuel_quantity')
            fuel_cost = request.form.get('fuel_cost')
            mileage = request.form.get('mileage')
            
            # Проверяем наличие всех необходимых данных
            if not all([date, fuel_quantity, fuel_cost, mileage]):
                flash('Пожалуйста, заполните все поля', 'danger')
                return redirect(url_for('edit_fuel', id=id))
            
            # Обновляем запись
            record.date = datetime.strptime(date, '%Y-%m-%d')
            record.fuel_quantity = float(fuel_quantity)
            record.fuel_cost = float(fuel_cost)
            record.mileage = float(mileage)
            
            db.session.commit()
            flash('Запись о заправке успешно обновлена', 'success')
            return redirect(url_for('fuel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при обновлении записи: {str(e)}', 'danger')
            return redirect(url_for('edit_fuel', id=id))
    
    return render_template('edit_fuel.html', record=record)

@app.route('/delete_fuel/<int:id>', methods=['POST'])
@login_required
def delete_fuel(id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('fuel'))
    
    record = FuelRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Запись о заправке успешно удалена', 'success')
    return redirect(url_for('fuel'))

@app.route('/add_maintenance_bulk', methods=['GET', 'POST'])
@login_required
def add_maintenance_bulk():
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('maintenance'))
    
    vehicles = Vehicle.query.all()
    
    if request.method == 'POST':
        try:
            date = request.form.get('date')
            if not date:
                flash('Пожалуйста, укажите дату обслуживания', 'danger')
                return redirect(url_for('add_maintenance_bulk'))
            
            for vehicle in vehicles:
                description = request.form.get(f'description_{vehicle.id}')
                cost = request.form.get(f'cost_{vehicle.id}')
                mileage = request.form.get(f'mileage_{vehicle.id}')
                next_mileage = request.form.get(f'next_mileage_{vehicle.id}')
                
                # Пропускаем пустые записи
                if not (description and cost and mileage):
                    continue
                
                maintenance_record = MaintenanceRecord(
                    vehicle_id=vehicle.id,
                    date=datetime.strptime(date, '%Y-%m-%d'),
                    description=description,
                    mileage=float(mileage),
                    cost=float(cost),
                    next_maintenance_mileage=float(next_mileage) if next_mileage else None
                )
                db.session.add(maintenance_record)
            
            db.session.commit()
            flash('Записи о техническом обслуживании успешно добавлены', 'success')
            return redirect(url_for('maintenance'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при добавлении записей: {str(e)}', 'danger')
            return redirect(url_for('add_maintenance_bulk'))
    
    return render_template('add_maintenance_bulk.html', vehicles=vehicles)

@app.route('/delete_maintenance/<int:id>', methods=['POST'])
@login_required
def delete_maintenance(id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для выполнения этой операции', 'danger')
        return redirect(url_for('maintenance'))
    
    record = MaintenanceRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Запись о техническом обслуживании успешно удалена', 'success')
    return redirect(url_for('maintenance'))

@app.route('/users')
@login_required
def users():
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/profile')
@login_required
def profile():
    # Получаем статистику для пользователя
    # Для обычных пользователей показываем только общую статистику
    total_fuelings = FuelRecord.query.count()
    total_maintenance = MaintenanceRecord.query.count()
    
    # Для администраторов и менеджеров получаем дополнительную статистику
    if current_user.role in ['admin', 'manager']:
        total_vehicles = Vehicle.query.count()
        total_expenses = db.session.query(
            db.func.coalesce(db.func.sum(FuelRecord.fuel_cost), 0) + 
            db.func.coalesce(db.func.sum(MaintenanceRecord.cost), 0)
        ).scalar()
    else:
        total_vehicles = 0
        total_expenses = 0
    
    return render_template('profile.html',
                         total_fuelings=total_fuelings,
                         total_maintenance=total_maintenance,
                         total_vehicles=total_vehicles,
                         total_expenses=total_expenses)

@app.route('/user/<int:id>')
@login_required
def user_data(id):
    if current_user.role not in ['admin', 'manager']:
        flash('У вас нет прав для доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    return render_template('user_details.html', user=user)

@app.route('/fuel/<int:id>')
@login_required
def view_fuel(id):
    record = FuelRecord.query.get_or_404(id)
    return render_template('view_fuel.html', record=record)

@app.route('/maintenance/<int:id>')
@login_required
def view_maintenance(id):
    record = MaintenanceRecord.query.get_or_404(id)
    return render_template('view_maintenance.html', record=record)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password, current_password):
        flash('Текущий пароль введен неверно', 'danger')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('Новые пароли не совпадают', 'danger')
        return redirect(url_for('profile'))
    
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Пароль успешно изменен', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)
