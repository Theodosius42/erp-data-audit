"""Tests unitaires pour les validateurs qualité."""

import pandas as pd
import pytest

from analyse_qualite.validators.clients import (
    _check_city_variants,
    _check_code_postal,
    _check_duplicates,
    _check_email,
    _check_siret,
)
from analyse_qualite.validators.affaires import _check_date_inversion
from analyse_qualite.validators.tarifs import _check_negative_prices, _check_duplicate_tarifs


class TestSiretValidation:
    def test_valid_siret(self):
        df = pd.DataFrame({
            "client_id": ["C1", "C2"],
            "siret": ["12345678901234", "98765432109876"],
        })
        issues = _check_siret(df)
        assert len(issues) == 0

    def test_invalid_siret_too_short(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "siret": ["1234567890"],
        })
        issues = _check_siret(df)
        assert len(issues) == 1
        assert issues[0].severity == "critique"
        assert "C1" in issues[0].affected_ids

    def test_siret_with_letters(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "siret": ["1234567890ABCD"],
        })
        issues = _check_siret(df)
        assert len(issues) == 1

    def test_empty_siret_ignored(self):
        df = pd.DataFrame({
            "client_id": ["C1", "C2"],
            "siret": ["", "12345678901234"],
        })
        issues = _check_siret(df)
        assert len(issues) == 0


class TestEmailValidation:
    def test_valid_email(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "email": ["test@example.com"],
        })
        issues = _check_email(df)
        assert len(issues) == 0

    def test_invalid_email_no_at(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "email": ["testexample.com"],
        })
        issues = _check_email(df)
        assert len(issues) == 1
        assert issues[0].severity == "majeur"

    def test_empty_email_ignored(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "email": [""],
        })
        issues = _check_email(df)
        assert len(issues) == 0


class TestCodePostal:
    def test_valid_cp(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "code_postal": ["37000"],
        })
        issues = _check_code_postal(df)
        assert len(issues) == 0

    def test_cp_too_short(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "code_postal": ["3700"],
        })
        issues = _check_code_postal(df)
        assert len(issues) == 1


class TestCityVariants:
    def test_canonical_city_ok(self):
        df = pd.DataFrame({
            "client_id": ["C1"],
            "ville": ["Tours"],
        })
        issues = _check_city_variants(df)
        assert len(issues) == 0

    def test_variant_detected(self):
        df = pd.DataFrame({
            "client_id": ["C1", "C2"],
            "ville": ["TOURS", "St-Avertin"],
        })
        issues = _check_city_variants(df)
        assert len(issues) == 1
        assert len(issues[0].affected_ids) == 2


class TestDuplicates:
    def test_no_duplicates(self):
        df = pd.DataFrame({
            "client_id": ["C1", "C2"],
            "raison_sociale": ["Dupont SARL", "Martin SAS"],
        })
        issues = _check_duplicates(df)
        assert len(issues) == 0

    def test_duplicate_detected(self):
        df = pd.DataFrame({
            "client_id": ["C1", "C2", "C3"],
            "raison_sociale": ["Dupont SARL", "  DUPONT  ", "Martin SAS"],
        })
        issues = _check_duplicates(df)
        assert len(issues) == 1
        assert "C1" in issues[0].affected_ids
        assert "C2" in issues[0].affected_ids


class TestDateInversion:
    def test_normal_dates(self):
        df = pd.DataFrame({
            "affaire_id": ["A1"],
            "date_debut": ["2024-01-01"],
            "date_fin": ["2024-12-31"],
        })
        issues = _check_date_inversion(df)
        assert len(issues) == 0

    def test_inverted_dates(self):
        df = pd.DataFrame({
            "affaire_id": ["A1"],
            "date_debut": ["2025-06-01"],
            "date_fin": ["2024-01-01"],
        })
        issues = _check_date_inversion(df)
        assert len(issues) == 1
        assert issues[0].severity == "critique"


class TestNegativePrices:
    def test_positive_price_ok(self):
        df = pd.DataFrame({
            "tarif_id": ["T1"],
            "prix_unitaire_ht": ["10.50"],
        })
        issues = _check_negative_prices(df)
        assert len(issues) == 0

    def test_negative_price_flagged(self):
        df = pd.DataFrame({
            "tarif_id": ["T1", "T2"],
            "prix_unitaire_ht": ["-5.00", "10.50"],
        })
        issues = _check_negative_prices(df)
        assert len(issues) == 1
        assert "T1" in issues[0].affected_ids


class TestDuplicateTarifs:
    def test_no_conflict(self):
        df = pd.DataFrame({
            "tarif_id": ["T1", "T2"],
            "produit_id": ["P1", "P2"],
            "client_id": ["C1", "C1"],
            "prix_unitaire_ht": ["10.0", "20.0"],
        })
        issues = _check_duplicate_tarifs(df)
        assert len(issues) == 0

    def test_conflict_detected(self):
        df = pd.DataFrame({
            "tarif_id": ["T1", "T2"],
            "produit_id": ["P1", "P1"],
            "client_id": ["C1", "C1"],
            "prix_unitaire_ht": ["10.0", "15.0"],
        })
        issues = _check_duplicate_tarifs(df)
        assert len(issues) == 1
        assert issues[0].severity == "critique"
