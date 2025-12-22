import sys
import os
from fastapi.testclient import TestClient

# Trik navigasi, agar folder test bisa melihat folder bakckend
current_file_dir = os.path.dirname(os.path.abspath(__file__))

root_project = os.path.join(current_file_dir, "..")

backend_folder = os.path.join(root_project, "backend")

sys.path.insert(0, root_project) # agar bisa from backend.main
sys.path.insert(0, backend_folder) # supaya bisa main.py 'from routers'

# import app dari main.py
from backend.main import app

# membuat client (pengganti postman)
client = TestClient(app)

# skenario 1 cek health
def test_read_root():
    #simulasi user nembak GET ke "/"
    response = client.get("/")

    # assert (tuntutan) memastikan status code 200 OK(bukan 404, 500)
    assert response.status_code == 200

    # sesuaikan teks di dalam dictionary, pastikan sesuai dengan isi endpoint get "/"
    # kalau di main py return {"message": "Hello world"} tulis sama persis
    assert response.json() == {"message": "Hello World"}