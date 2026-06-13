from app_simple import app, db, Potrero, Animal
with app.app_context():
    potreros = Potrero.query.all()
    for p in potreros:
        ocupantes = Animal.query.filter(Animal.potrero_id == p.id, Animal.estado.notin_(['vendido', 'fallecido', 'muerto'])).count()
        print(f"Potrero {p.nombre}: capacidad {p.capacidad}, ocupantes {ocupantes}")
