import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from backend.main import app
from backend.database import get_session


# setup database RAM
@pytest.fixture(name="session")
def session_fixture():
    # buat mesin database di RAM
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # setelah tes selesai akan bersih bersih otomatis

@pytest.fixture(name="client")
def client_fixture(session: Session):
    # override fungsi
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client

    # cabut override setelah selesai
    app.dependency_overrides.clear()

# setup token/login
@pytest.fixture(name="token")
def token_fixture(client: TestClient): 
    # register user dummy
    reg_payload = {
        "email": "fixture@gmail.com",
        "name": "fixture_login",
        "age": 21,
        "password": "fixturepassword21"
    } 
    reg_response = client.post("/register", json=reg_payload)

    # debugging untuk mengetahui errornya
    if reg_response.status_code != 200:
        print("\nFixture Register Error:", reg_response())
    assert reg_response.status_code == 200

    # login user dummy
    login_payload = {
        "username": "fixture_login",
        "password": "fixturepassword21"
    }
    login_response = client.post("/token", data=login_payload)

    # debugging error
    if login_response.status_code != 200:
        print("\nFixture Login error:", login_response.json())
    assert login_response.status_code == 200

    return login_response.json()["access_token"]
