from app_simple import app, db, Potrero, Animal
with app.app_context():
    potrero_id = 3 # Potrero Sur with capacity 1
    # Get an existing animal not in this potrero
    animal = Animal.query.filter(Animal.potrero_id != potrero_id).first()
    
    print("Modifying animal potrero_id to", potrero_id)
    animal.potrero_id = potrero_id
    
    potrero_obj = Potrero.query.get(potrero_id)
    ocupantes = Animal.query.filter(Animal.potrero_id == potrero_id, Animal.estado.notin_(['vendido', 'fallecido', 'muerto'])).count()
    
    print(f"Ocupantes = {ocupantes}, capacidad = {potrero_obj.capacidad}")
    print(f"Ocupantes >= capacidad is {ocupantes >= potrero_obj.capacidad}")
