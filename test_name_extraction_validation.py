import pytest
from fastapi.testclient import TestClient

from chatbot_ai_service.main import app


client = TestClient(app)
TENANT_ID = "473173"


@pytest.mark.parametrize(
    "message,expected_name",
    [
        ("Juan", "Juan"),  # Nombre
        ("Juan Pérez", "Juan Pérez"),  # Nombre + apellido
        ("María José", "María José"),  # Nombre compuesto
        ("Ana Gómez López", "Ana Gómez López"),  # Nombre + dos apellidos
        ("Carlos Alberto", "Carlos Alberto"),  # Dos nombres

        ("Soy Juan", "Juan"),
        ("Soy Juan Pérez", "Juan Pérez"),
        ("Soy María José", "María José"),
        ("Soy Ana Gómez López", "Ana Gómez López"),

        ("Me llamo Juan", "Juan"),
        ("Me llamo Juan Pérez", "Juan Pérez"),
        ("Me llamo María José", "María José"),
        ("Me llamo Ana Gómez López", "Ana Gómez López"),

        ("Claro, mi nombre es Juan", "Juan"),
        ("Claro, mi nombre es Juan Pérez", "Juan Pérez"),
        ("Claro, mi nombre es María José", "María José"),
        ("Claro, mi nombre es Ana Gómez López", "Ana Gómez López"),

        ("Nombre: Juan", "Juan"),
        ("Nombre: Juan Pérez", "Juan Pérez"),
        ("Nombre es María José", "María José"),
        ("Mi nombre es Carlos Alberto", "Carlos Alberto"),
    ],
)
def test_extract_user_name_variations(message: str, expected_name: str):
    resp = client.post(
        f"/api/v1/tenants/{TENANT_ID}/extract-user-name",
        json={"message": message},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("is_valid") is True, data
    assert data.get("name") == expected_name, data


@pytest.mark.parametrize(
    "name_text",
    [
        "Juan",
        "Juan Pérez",
        "María José",
        "Ana María García",
        "Carlos Alberto Pérez",
        "Lucía",
        "José Luis",
    ],
)
def test_validate_name_positive(name_text: str):
    resp = client.post(
        f"/api/v1/tenants/{TENANT_ID}/validate-data",
        json={"data": name_text, "data_type": "name"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("is_valid") is True, data


@pytest.mark.parametrize(
    "message",
    [
        "hola",
        "gracias",
        "referido",
        "123456",
        "K351ERXL",
    ],
)
def test_validate_name_negative_words_and_codes(message: str):
    resp = client.post(
        f"/api/v1/tenants/{TENANT_ID}/validate-data",
        json={"data": message, "data_type": "name"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("is_valid") is False, data


