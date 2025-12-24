from backend.main import app

# skenario 1 cek health
def test_read_root(client):
    #simulasi user nembak GET ke "/"
    response = client.get("/")

    # assert (tuntutan) memastikan status code 200 OK(bukan 404, 500)
    assert response.status_code == 200

    # sesuaikan teks di dalam dictionary, pastikan sesuai dengan isi endpoint get "/"
    # kalau di main py return {"message": "Hello world"} tulis sama persis
    assert response.json() == {"message": "Hello World"}

# skenario 2 register user
def test_create_user(client):
    # data pendaftaran
    payload = {
        "email": "ajip23@gmail.com",
        "name": "aji_tes_buat",
        "age": 21,
        "password": "ajipurnama123"
    }

    # tembak endpoint register (POST)
    # sesuaikan dengan URL "/register" yg ada di routers
    response = client.post("/register", json=payload)
    print("PESAN DARI SERVER :", response.json())

    # 'assert' untuk mengecek/melakukan validasi akhir Sukses (200 OK) atau (201 Created) sesuaikan
    assert response.status_code == 200

    data = response.json()
    assert data ["email"] == "ajip23@gmail.com"
    assert "id" in data  # pastikan dia (data user) punya id yg otomatis di berikan DB (artinya masuk DB)
    assert "password" not in data # pastikan agar password tidak dikembalikan ke user(security)

# skenario 3 cek token login akses
def test_login_user(client):
    # register usernya biar ada di database dan harus beda email dan name-nya
    client.post("/register", json={
        "email": "ajip234@gmail.com",
        "name": "aji_tes_login",
        "age": 23,
        "password": "ajipurnama123"
    })

    # siapkan payload login
    # key-nya harus "username" (karena aturan FastAPI)
    # valuenya adalah "aji_tes_login" (karena logikanya login pakai name yg akan berubah menjadi username)
    login_payload = {
        "username": "aji_tes_login",
        "password": "ajipurnama123"
    }
    # tembak endpoint pakai data=..., bukan json=...
    response = client.post("/token", data=login_payload)

    # cek hasil
    print("\nRESPONSE LOGIN:", response.json())
    assert response.status_code == 200
    assert "access_token" in response.json()

# skenario 4 CRUD notes
def test_create_notes(client, token):
    # bisa langsung pakai token dari fixture gaperlu login/regis manual

    # create note,  pastikan ada (header authorization) tanpa ini server error 401
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # siapkan data yg akan dimasukkan ke notes
    note_payload = {
        "title": "Aku programer",
        "content": "percobaan pertama"
    }
    response = client.post("/notes", json=note_payload, headers=headers)

    print("\nResponse Notes", response.json())

    # validasi (assert)
    assert response.status_code==200
    data = response.json()
    assert data["title"] == "Aku programer"
    assert "id" in data
    assert "owner_id" in data