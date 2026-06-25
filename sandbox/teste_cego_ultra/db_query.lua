-- DB
function buscarPlayer(nome)
    db.query(string.format("SELECT * FROM players WHERE name = '%s'", nome))
end