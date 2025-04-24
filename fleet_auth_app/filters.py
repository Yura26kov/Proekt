def translate_vehicle_type(vehicle_type):
    translations = {
        'car': 'Легковой автомобиль',
        'truck': 'Грузовик',
        'bus': 'Автобус',
        'special': 'Спецтехника',
        'minivan': 'Минивэн',
        'suv': 'Внедорожник',
        'pickup': 'Пикап',
        'van': 'Фургон',
        'trailer': 'Прицеп',
        'motorcycle': 'Мотоцикл',
        'excavator': 'Экскаватор',
        'bulldozer': 'Бульдозер',
        'crane': 'Кран',
        'Car': 'Легковой автомобиль',
        'Truck': 'Грузовик',
        'Van': 'Фургон',
        'Bus': 'Автобус'
    }
    return translations.get(vehicle_type, vehicle_type) 