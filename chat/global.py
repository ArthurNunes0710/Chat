from app import app, db, Conversa
# cria o chat global eu instancio ele direto aqui pq quando cria usuario eu queria q ele automaticamente participasse do global
with app.app_context():

    global_chat = Conversa(
        nome="Global",
        tipo="global"
    )

    db.session.add(global_chat)
    db.session.commit()

    print("Chat global")