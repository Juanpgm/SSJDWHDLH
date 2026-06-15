from io import BytesIO

import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient


class TestTables:
    def test_list_tables_returns_ok(self, client: TestClient) -> None:
        response = client.get("/tables")
        assert response.status_code in {200, 503}

    def test_unknown_table_returns_404(self, client: TestClient) -> None:
        response = client.get("/tables/nonexistent_table/data")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Requires DB connection")
    def test_homicidios_schema(self, client: TestClient) -> None:
        response = client.get("/tables/homicidios/schema")
        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires DB connection")
    def test_homicidios_parquet_download(self, client: TestClient) -> None:
        response = client.get("/tables/homicidios/download/parquet")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-parquet"

        table = pq.read_table(BytesIO(response.content))
        assert table.num_columns > 0

    @pytest.mark.skip(reason="Requires DB connection")
    def test_homicidios_csv_download(self, client: TestClient) -> None:
        response = client.get("/tables/homicidios/download/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
