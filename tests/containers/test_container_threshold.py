import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy import select, text
from app.modules.containers.models import (Container, ContainerFullEvent, ContainerCitizenReport)
from tests.containers.conftest import TestingSessionLocal
from app.modules.containers.service import ContainerThresholdService

BASE_URL = "/api/v1/containers"

@pytest.fixture
# Crear un contenedor nuevo para cada prueba
def container_id(client):
    """Crea un contenedor nuevo para cada prueba."""

    response = client.post(
        f"{BASE_URL}/",
        json={
            "code": "CONT-THRESHOLD-TEST",
            "name": "Contenedor para pruebas de umbral",
            "address": "Alameda de los Descalzos, Rimac",
            "latitude": -12.0365,
            "longitude": -77.0241,
            "capacity_kg": 150
        }
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]

# Función auxiliar para reportar un contenedor lleno
def report(client, container_id, citizen_id):
    return client.post(
        f"{BASE_URL}/{container_id}/report-full",
        json={"citizen_id": citizen_id}
    )

# Tests para la funcionalidad de reportar contenedores llenos
def test_first_report(client, container_id):
    response = report(client, container_id, 10)

    assert response.status_code == 200
    data = response.json()

    assert data["reports_registered"] == 1
    assert data["current_status"] == "DISPONIBLE"
    assert data["ready_for_tsp_collection"] is False

# Tests para verificar que el umbral cambia el estado del contenedor
def test_threshold_changes_status(client, container_id):
    for citizen_id in (10, 11, 12):
        response = report(client, container_id, citizen_id)
        assert response.status_code == 200

    data = response.json()

    assert data["reports_registered"] == 3
    assert data["current_status"] == "LLENO"
    assert data["ready_for_tsp_collection"] is True

# Tests para verificar que un ciudadano no puede reportar dos veces el mismo contenedor
def test_duplicate_vote(client, container_id):
    first = report(client, container_id, 10)
    second = report(client, container_id, 10)

    assert first.status_code == 200
    assert second.status_code == 409

    with TestingSessionLocal() as db:
        container = db.get(Container, container_id)

        assert container.current_reports_count == 1

        votes = db.scalars(
            select(ContainerCitizenReport).where(
                ContainerCitizenReport.container_id == container_id
            )
        ).all()

        assert len(votes) == 1

# Tests para verificar que un contenedor lleno no acepta más reportes
def test_full_container_rejects_more_reports(
    client, container_id
):
    for citizen_id in (10, 11, 12):
        assert report(
            client, container_id, citizen_id
        ).status_code == 200

    response = report(client, container_id, 13)

    assert response.status_code == 409

    with TestingSessionLocal() as db:
        container = db.get(Container, container_id)
        assert container.current_reports_count == 3

# Tests para verificar que un contenedor inactivo no acepta reportes
def test_invalid_citizen_id(client, container_id):
    response = report(client, container_id, 0)

    assert response.status_code == 422

# Tests para verificar que un contenedor inexistente no acepta reportes
def test_nonexistent_container(client):
    response = report(client, 999999, 10)

    assert response.status_code == 404

# Tests para verificar que un contenedor inactivo no acepta reportes
def test_inactive_container(client, container_id):
    response = client.delete(
        f"{BASE_URL}/{container_id}"
    )
    assert response.status_code in (200, 204)

    response = report(client, container_id, 10)

    assert response.status_code == 404

# Tests para verificar que múltiples reportes concurrentes no pierdan actualizaciones
def test_concurrent_reports(container_id):
    """
    Verifica que tres ciudadanos distintos puedan
    reportar simultáneamente sin perder actualizaciones.
    """

    barrier = Barrier(3)

    def submit_vote(citizen_id):
        with TestingSessionLocal() as db:
            service = ContainerThresholdService(db)

            barrier.wait(timeout=10)

            return service.report_container_full(
                container_id=container_id,
                citizen_id=citizen_id
            )

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(submit_vote, citizen_id)
            for citizen_id in (10, 11, 12)
        ]

        results = [
            future.result(timeout=20)
            for future in futures
        ]

    assert len(results) == 3

    with TestingSessionLocal() as db:
        container = db.get(Container, container_id)

        assert container.current_reports_count == 3
        assert container.status == "LLENO"

        votes = db.scalars(
            select(ContainerCitizenReport).where(
                ContainerCitizenReport.container_id == container_id
            )
        ).all()

        assert len(votes) == 3

# Tests para verificar que un ciudadano no pueda reportar dos veces el mismo contenedor de manera concurrente
def test_concurrent_duplicate_votes(container_id):
    """
    Dos peticiones simultáneas del mismo ciudadano
    deben producir un solo voto válido.
    """
    from fastapi import HTTPException

    barrier = Barrier(2)

    def submit_vote():
        with TestingSessionLocal() as db:
            service = ContainerThresholdService(db)
            barrier.wait(timeout=10)

            try:
                result = service.report_container_full(
                    container_id=container_id,
                    citizen_id=50
                )
                return 200, result
            except HTTPException as exc:
                return exc.status_code, exc.detail

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(submit_vote)
            for _ in range(2)
        ]
        results = [
            future.result(timeout=20)
            for future in futures
        ]

    codes = sorted(code for code, _ in results)

    assert codes == [200, 409]

    with TestingSessionLocal() as db:
        container = db.get(Container, container_id)

        assert container.current_reports_count == 1

        votes = db.scalars(
            select(ContainerCitizenReport).where(
                ContainerCitizenReport.container_id == container_id
            )
        ).all()

        assert len(votes) == 1

# Tests para verificar que un contenedor lleno genera un evento de "contenedor lleno"
def test_full_container_generates_one_event(client, container_id):
    # Reportar dos veces sin alcanzar el umbral no genera evento
    for citizen_id in (10, 11):
        response = report(client, container_id, citizen_id)
        assert response.status_code == 200

    with TestingSessionLocal() as db:
        events = db.scalars(
            select(ContainerFullEvent).where(
                ContainerFullEvent.container_id == container_id
            )
        ).all()

        assert len(events) == 0

    # El tercer reporte alcanza el umbral y genera un evento
    response = report(client, container_id, 12)

    assert response.status_code == 200
    assert response.json()["current_status"] == "LLENO"

    with TestingSessionLocal() as db:
        events = db.scalars(
            select(ContainerFullEvent).where(
                ContainerFullEvent.container_id == container_id
            )
        ).all()

        assert len(events) == 1
        assert events[0].event_type == "container.full"
        assert events[0].processed_at is None

    # Un cuarto reporte no genera un segundo evento
    response = report(client, container_id, 13)
    assert response.status_code == 409

    with TestingSessionLocal() as db:
        events = db.scalars(
            select(ContainerFullEvent).where(
                ContainerFullEvent.container_id == container_id
            )
        ).all()

        assert len(events) == 1