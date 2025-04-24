from app import app, db
from models import User, Vehicle, FuelRecord, MaintenanceRecord
from werkzeug.security import generate_password_hash
import os

def init_db():
    with app.app_context():
        # Удаляем существующую базу данных, если она есть
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fleet.db')
        if os.path.exists(db_file):
            os.remove(db_file)
            print('Старая база данных удалена')
        
        # Создаем все таблицы
        db.create_all()
        print('Созданы все таблицы')
        
        # Создаем тестового администратора
        admin = User(
            username='admin',
            password=generate_password_hash('admin'),
            role='admin',
            email='admin@example.com',
            phone='+79001234567'
        )
        db.session.add(admin)
        
        # Создаем тестового менеджера
        manager = User(
            username='manager',
            password=generate_password_hash('manager'),
            role='manager',
            email='manager@example.com',
            phone='+79001234568'
        )
        db.session.add(manager)
        
        # Создаем тестового пользователя
        user = User(
            username='user',
            password=generate_password_hash('user'),
            role='user',
            email='user@example.com',
            phone='+79001234569'
        )
        db.session.add(user)
        
        db.session.commit()
        print('Созданы тестовые пользователи:')
        print('Администратор: admin/admin')
        print('Менеджер: manager/manager')
        print('Пользователь: user/user')

if __name__ == '__main__':
    init_db() 