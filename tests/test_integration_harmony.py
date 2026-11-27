from datetime import datetime
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.modules.waste_reports.router import get_waste_report_service
from app.modules.waste_reports.service import (
    InvalidWasteReportLocation,
    WasteReportAlreadyResolved,
    WasteReportNotFound,
)


class InMemoryWasteReportService:
    def __init__(self):
        self.items = []

    def create_waste_report(self, payload):
        if not (-12.05 <= payload.latitude <= -12.00 and -77.06 <= payload.longitude <= -77.00):
            raise InvalidWasteReportLocation("La ubicación debe estar dentro del Rímac")
        item = SimpleNamespace(
            id=len(self.items) + 1,
            citizen_id=payload.citizen_id,
            description=payload.description,
            photo_evidence_url=payload.photo_evidence_url,
            address_reference=payload.address_reference,
            latitude=payload.latitude,
            longitude=payload.longitude,
            status="PENDIENTE",
            created_at=datetime.utcnow(),
        )
        self.items.append(item)
        return item

    def list_reports(self, status_filter=None):
        if status_filter is None:
            return list(self.items)
        return [item for item in self.items if item.status == status_filter]

    def resolve_report(self, report_id: int):
        target = next((item for item in self.items if item.id == report_id), None)
        if target is None:
            raise WasteReportNotFound("La denuncia no existe")
        if target.status == "ATENDIDA":
            raise WasteReportAlreadyResolved("La denuncia ya fue atendida")
        target.status = "ATENDIDA"
        return target


def test_all_module_routes_and_static_portal_are_mounted():
    client = TestClient(app)
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    for prefix in (
        "/api/v1/auth/login",
        "/api/v1/containers/",
        "/api/v1/containers/flyweight-specs",
        "/api/v1/routes/optimal-daily",
        "/api/v1/drop-and-go/requests",
        "/api/v1/drop-and-go/notifications/{citizen_id}",
        "/api/v1/governance/staff",
        "/api/v1/waste-reports/pending",
        "/api/v1/waste-reports/{report_id}/resolve",
        "/api/v1/plant/material-specs",
        "/api/v1/plant/packages/pending",
        "/api/v1/plant/packages/{package_code}/process",
    ):
        assert prefix in paths

    for page in (
        "/app/index.html",
        "/app/acceso-personal.html",
        "/app/ciudadano.html",
        "/app/conductor.html",
        "/app/operario.html",
        "/app/admin.html",
        "/app/denuncias.html",
    ):
        assert client.get(page).status_code == 200


def test_waste_reports_create_list_and_resolve_contract():
    service = InMemoryWasteReportService()
    app.dependency_overrides[get_waste_report_service] = lambda: service
    client = TestClient(app)
    try:
        invalid_res = client.post(
            "/api/v1/waste-reports/",
            json={
                "citizen_id": 1,
                "description": "Basura fuera de rango",
                "photo_evidence_url": "data:image/jpeg;base64,abc",
                "address_reference": "Lima Cercado",
                "latitude": -12.10,
                "longitude": -77.03,
            },
        )
        assert invalid_res.status_code == 422

        created_res = client.post(
            "/api/v1/waste-reports/",
            json={
                "citizen_id": 1,
                "description": "Desmonte en esquina",
                "photo_evidence_url": "data:image/jpeg;base64,abc",
                "address_reference": "Av. Alcázar cdra. 4",
                "latitude": -12.0271,
                "longitude": -77.0315,
            },
        )
        assert created_res.status_code == 201
        report_id = created_res.json()["id"]

        pending_res = client.get("/api/v1/waste-reports/pending")
        assert pending_res.status_code == 200
        assert len(pending_res.json()) == 1

        resolved_res = client.patch(f"/api/v1/waste-reports/{report_id}/resolve")
        assert resolved_res.status_code == 200
        assert resolved_res.json()["status"] == "ATENDIDA"

        duplicate_resolve = client.patch(f"/api/v1/waste-reports/{report_id}/resolve")
        assert duplicate_resolve.status_code == 409

        missing_resolve = client.patch("/api/v1/waste-reports/999/resolve")
        assert missing_resolve.status_code == 404

        assert client.get("/api/v1/waste-reports/pending").json() == []
    finally:
        app.dependency_overrides.clear()
