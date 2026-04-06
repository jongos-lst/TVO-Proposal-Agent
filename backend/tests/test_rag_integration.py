"""Tests for RAG integration: ingestion, search, competitor scraping, and fallback."""

import json
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from app.services.rag import (
    ingest_text,
    search_knowledge,
    search_or_scrape,
    get_vectorstore,
    NO_RESULTS_MSG,
    _results_mention_competitor,
)
from app.services.competitor_scraper import (
    scrape_competitor_page,
    scrape_competitor_for_rag,
    save_competitor_knowledge,
    web_search_competitor,
    add_competitor_to_catalog,
)


@pytest.fixture(autouse=True)
def isolated_chroma(tmp_path):
    """Use a fresh ephemeral ChromaDB for each test to avoid cross-contamination."""
    import app.services.rag as rag_module
    rag_module._vectorstore = None  # reset singleton

    with patch.object(rag_module, "get_vectorstore") as mock_vs:
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vs = Chroma(
            collection_name="test_knowledge",
            embedding_function=embeddings,
            persist_directory=str(tmp_path / "chroma_test"),
        )
        mock_vs.return_value = vs
        yield vs


class TestIngestText:
    def test_ingest_returns_chunk_count(self):
        count = ingest_text("This is a test document about Dell Latitude failures.", source="test")
        assert count >= 1

    def test_ingest_empty_string(self):
        count = ingest_text("", source="test")
        assert count == 0

    def test_ingest_long_text_splits(self):
        long_text = "Dell Latitude has high failure rates. " * 100
        count = ingest_text(long_text, source="test")
        assert count > 1  # should split into multiple chunks


class TestSearchKnowledge:
    def test_search_after_ingest(self):
        ingest_text(
            "The Dell Latitude 5430 Rugged has an 8% annual failure rate "
            "compared to Getac B360's 2% failure rate. Dell is semi-rugged only.",
            source="test_dell",
        )
        result = search_knowledge("Dell failure rate comparison", k=2)
        assert result != NO_RESULTS_MSG
        assert "Dell" in result or "failure" in result

    def test_search_empty_db(self):
        result = search_knowledge("anything at all")
        assert result == NO_RESULTS_MSG


class TestResultsRelevanceCheck:
    """Test _results_mention_competitor — prevents returning wrong-competitor data."""

    def test_exact_match(self):
        assert _results_mention_competitor(
            "Dell Latitude 5430 has 8% failure rate", "Dell Latitude 5430"
        )

    def test_partial_match_two_parts(self):
        assert _results_mention_competitor(
            "Dell Latitude semi-rugged comparison", "Dell Latitude 5430"
        )

    def test_wrong_competitor_rejected(self):
        assert not _results_mention_competitor(
            "Panasonic Toughbook 40 weighs 3.5kg", "Durabook S15"
        )

    def test_wrong_competitor_different_brands(self):
        assert not _results_mention_competitor(
            "HP EliteBook has no rugged rating", "Lenovo ThinkPad X1"
        )

    def test_single_word_brand(self):
        # "Zebra" has only one significant part
        assert _results_mention_competitor(
            "Zebra tablets for warehouse use", "Zebra ET80"
        )

    def test_triggers_scrape_for_irrelevant_rag(self):
        """The core bug: RAG returns Panasonic data for a Durabook query."""
        # Seed ChromaDB with Panasonic data
        ingest_text(
            "Panasonic Toughbook 40 weighs 3.5kg and has IP66 rating.",
            source="test_panasonic",
        )
        # Ask about Durabook — RAG will return Panasonic (wrong), should trigger scrape
        mock_content = "# Durabook S15\n## Specs\n- Weight: 2.5 kg"
        with patch(
            "app.services.competitor_scraper.scrape_competitor_for_rag",
            return_value=mock_content,
        ) as mock_scrape:
            result = search_or_scrape(
                "Durabook S15 device failures", competitor_name="Durabook S15", k=4
            )
            mock_scrape.assert_called_once_with("Durabook S15")


class TestSearchOrScrape:
    def test_returns_rag_results_when_available(self):
        ingest_text(
            "Panasonic Toughbook 40 weighs 3.5kg and costs $3899. "
            "It has IP66 rating but is significantly heavier than Getac alternatives.",
            source="test_panasonic",
        )
        result = search_or_scrape("Panasonic weight comparison", competitor_name=None, k=2)
        assert result != NO_RESULTS_MSG
        assert "Panasonic" in result or "weight" in result or "3.5" in result

    def test_fallback_scrape_when_empty(self):
        """When RAG is empty and competitor_name given, should attempt scrape."""
        mock_content = "# Scraped: Dell Latitude\n## Specs\n- Processor: Intel i7"
        with patch(
            "app.services.competitor_scraper.scrape_competitor_for_rag",
            return_value=mock_content,
        ) as mock_scrape:
            result = search_or_scrape("Dell specs", competitor_name="Dell Latitude 5430", k=2)
            mock_scrape.assert_called_once_with("Dell Latitude 5430")
            # After scrape + ingest, search should find something
            assert result != NO_RESULTS_MSG or "Dell" in result

    def test_no_scrape_without_competitor_name(self):
        """When competitor_name is None, should not attempt scrape."""
        result = search_or_scrape("anything", competitor_name=None, k=2)
        assert result == NO_RESULTS_MSG


class TestCompetitorScraper:
    def test_scrape_competitor_page_with_mock(self):
        html = """
        <html><body>
        <h1>Dell Latitude 5430 Rugged</h1>
        <p>14" FHD display with 1000 nits brightness</p>
        <p>Intel Core i7-1365U processor</p>
        <p>MIL-STD-810H, IP53 rated</p>
        <p>Weight: 2.07 kg</p>
        <p>Operating temperature: -29°C to 63°C</p>
        <ul>
            <li>Semi-rugged design for field deployment</li>
            <li>Hot-swappable battery not available</li>
        </ul>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch("app.services.competitor_scraper.requests.get", return_value=mock_resp):
            result = scrape_competitor_page("https://example.com/dell", "Dell Latitude 5430")

        assert result is not None
        assert "Dell Latitude 5430" in result
        assert "MIL-STD-810H" in result

    def test_scrape_competitor_page_404(self):
        import requests as req
        with patch(
            "app.services.competitor_scraper.requests.get",
            side_effect=req.RequestException("404 Not Found"),
        ):
            result = scrape_competitor_page("https://example.com/bad", "NonExistent")
        assert result is None

    def test_scrape_competitor_page_empty_content(self):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>OK</body></html>"
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch("app.services.competitor_scraper.requests.get", return_value=mock_resp):
            result = scrape_competitor_page("https://example.com/empty", "Empty Product")
        assert result is None  # too short / no useful data


class TestCompetitorForRag:
    def test_name_matching_exact(self):
        """Full name match should find the competitor."""
        with patch(
            "app.services.competitor_scraper.scrape_competitor_page",
            return_value="# Mocked content",
        ) as mock_scrape:
            result = scrape_competitor_for_rag("Dell Latitude 5430 Rugged")
            assert result == "# Mocked content"
            mock_scrape.assert_called_once()

    def test_name_matching_partial(self):
        """Partial name match should still find the competitor."""
        with patch(
            "app.services.competitor_scraper.scrape_competitor_page",
            return_value="# Mocked content",
        ) as mock_scrape:
            result = scrape_competitor_for_rag("Dell Latitude")
            assert result == "# Mocked content"

    def test_unknown_competitor_triggers_web_search(self):
        """Unknown competitor should fall back to web search."""
        with patch(
            "app.services.competitor_scraper._web_search_and_scrape",
            return_value="# Web-searched content",
        ) as mock_ws:
            result = scrape_competitor_for_rag("Durabook S15 Rugged")
            mock_ws.assert_called_once_with("Durabook S15 Rugged")
            assert result == "# Web-searched content"

    def test_unknown_competitor_web_search_fails_gracefully(self):
        """If web search also fails, return None."""
        with patch(
            "app.services.competitor_scraper._web_search_and_scrape",
            return_value=None,
        ):
            result = scrape_competitor_for_rag("Totally Unknown Device 9000")
            assert result is None


class TestWebSearchCompetitor:
    def test_returns_url_from_search(self):
        mock_results = [
            {"href": "https://www.durabook.com/products/s15", "title": "S15"},
        ]
        with patch("app.services.competitor_scraper.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results
            url = web_search_competitor("Durabook S15")
            assert url == "https://www.durabook.com/products/s15"

    def test_prefers_manufacturer_domains(self):
        mock_results = [
            {"href": "https://blog.example.com/review-s15", "title": "Review"},
            {"href": "https://www.dell.com/products/latitude", "title": "Dell Latitude"},
        ]
        with patch("app.services.competitor_scraper.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results
            url = web_search_competitor("Dell Latitude")
            assert "dell.com" in url

    def test_returns_none_on_no_results(self):
        with patch("app.services.competitor_scraper.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = []
            url = web_search_competitor("Nonexistent Product")
            assert url is None

    def test_returns_none_when_ddgs_unavailable(self):
        """If duckduckgo-search is not installed (DDGS=None), returns None."""
        with patch("app.services.competitor_scraper.DDGS", None):
            url = web_search_competitor("Test Product")
            assert url is None


class TestAddCompetitorToCatalog:
    def test_adds_new_competitor(self, tmp_path):
        # Create a minimal competitors.json
        catalog_path = tmp_path / "competitors.json"
        catalog_path.write_text("[]")
        with patch("app.services.competitor_scraper.COMPETITORS_PATH", catalog_path):
            add_competitor_to_catalog("Durabook S15", "https://www.durabook.com/s15")
            data = json.loads(catalog_path.read_text())
            assert len(data) == 1
            assert data[0]["name"] == "Durabook S15"
            assert data[0]["product_url"] == "https://www.durabook.com/s15"
            assert data[0]["annual_failure_rate"] == 0.10

    def test_does_not_duplicate(self, tmp_path):
        catalog_path = tmp_path / "competitors.json"
        catalog_path.write_text(json.dumps([{
            "name": "Durabook S15",
            "category": "Rugged Laptop",
            "base_price": 2500.0,
            "warranty_standard": "3-year",
            "annual_failure_rate": 0.05,
            "product_url": "https://www.durabook.com/s15",
            "weaknesses": [],
        }]))
        with patch("app.services.competitor_scraper.COMPETITORS_PATH", catalog_path):
            add_competitor_to_catalog("Durabook S15", "https://www.durabook.com/s15-new")
            data = json.loads(catalog_path.read_text())
            assert len(data) == 1  # no duplicate added

    def test_updates_missing_url(self, tmp_path):
        catalog_path = tmp_path / "competitors.json"
        catalog_path.write_text(json.dumps([{
            "name": "Durabook S15",
            "category": "Rugged Laptop",
            "base_price": 2500.0,
            "warranty_standard": "3-year",
            "annual_failure_rate": 0.05,
            "weaknesses": [],
        }]))
        with patch("app.services.competitor_scraper.COMPETITORS_PATH", catalog_path):
            add_competitor_to_catalog("Durabook S15", "https://www.durabook.com/s15")
            data = json.loads(catalog_path.read_text())
            assert data[0]["product_url"] == "https://www.durabook.com/s15"


class TestSaveCompetitorKnowledge:
    def test_saves_markdown_file(self, tmp_path):
        with patch("app.services.competitor_scraper.KNOWLEDGE_DIR", tmp_path):
            path = save_competitor_knowledge("Dell Latitude 5430", "# Test content")
            assert path.exists()
            assert path.name == "scraped_dell_latitude_5430.md"
            assert path.read_text() == "# Test content"
