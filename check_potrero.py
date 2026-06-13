from app_simple import app, db, Potrero, Animal
with app.app_context():
    potreros = Potrero.query.filter_by(nombre='Potrero Sur').all()
    for p in potreros:
        print(f"Potrero ID: {p.id}, nombre: {p.nombre}, capacidad: {p.capacidad}")
        animales = Animal.query.filter_by(potrero_id=p.id).all()
        for a in animales:
            print(f"  Animal ID: {a.id}, nombre: {a.nombre}, estado: {a.estado}")
