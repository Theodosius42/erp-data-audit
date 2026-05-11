"""Tests unitaires pour le module de transformation."""

import pandas as pd
import pytest

from pipeline.transform import (
    TransformLog,
    deduplicate_clients,
    remap_client_references,
    transform_affaires,
    transform_clients,
    transform_produits,
    transform_tarifs,
)


@pytest.fixture
def tlog():
    return TransformLog()


class TestTransformClients:
    def _make_client(self, **overrides):
        base = {
            "client_id": "CLI-0001",
            "raison_sociale": "Test Company SARL",
            "statut_juridique": "SARL",
            "siret": "12345678901234",
            "adresse": "1 rue Test",
            "code_postal": "37000",
            "ville": "Tours",
            "telephone": "02 47 00 00 00",
            "email": "test@example.com",
            "secteur_activite": "Industrie",
            "conditions_paiement": "30 jours",
            "statut": "Actif",
            "date_creation_fiche": "2024-01-01",
            "commercial_referent": "P. Martin",
        }
        base.update(overrides)
        return base

    def test_city_standardization(self, tlog):
        df = pd.DataFrame([self._make_client(ville="TOURS")])
        result = transform_clients(df, tlog)
        assert result.iloc[0]["ville"] == "Tours"
        assert tlog.count == 1

    def test_whitespace_trim(self, tlog):
        df = pd.DataFrame([self._make_client(raison_sociale="  Test Corp  ")])
        result = transform_clients(df, tlog)
        assert result.iloc[0]["raison_sociale"] == "Test Corp"

    def test_siret_padding(self, tlog):
        df = pd.DataFrame([self._make_client(siret="1234567890")])
        result = transform_clients(df, tlog)
        assert result.iloc[0]["siret"] == "00001234567890"
        assert len(result.iloc[0]["siret"]) == 14

    def test_email_lowercase(self, tlog):
        df = pd.DataFrame([self._make_client(email="Test@Example.COM")])
        result = transform_clients(df, tlog)
        assert result.iloc[0]["email"] == "test@example.com"

    def test_code_postal_padding(self, tlog):
        df = pd.DataFrame([self._make_client(code_postal="3700")])
        result = transform_clients(df, tlog)
        assert result.iloc[0]["code_postal"] == "03700"

    def test_no_false_corrections(self, tlog):
        df = pd.DataFrame([self._make_client()])
        transform_clients(df, tlog)
        assert tlog.count == 0


class TestDeduplicateClients:
    def test_merges_duplicates(self, tlog):
        df = pd.DataFrame([
            {"client_id": "C1", "raison_sociale": "Dupont SARL", "ville": "Tours", "email": "a@b.com", "siret": "12345678901234",
             "statut_juridique": "SARL", "adresse": "1 rue X", "code_postal": "37000", "telephone": "0247000000",
             "secteur_activite": "Industrie", "conditions_paiement": "30j", "statut": "Actif", "date_creation_fiche": "2024-01-01", "commercial_referent": "P. Martin"},
            {"client_id": "C2", "raison_sociale": "DUPONT", "ville": "", "email": "", "siret": "",
             "statut_juridique": "", "adresse": "", "code_postal": "", "telephone": "",
             "secteur_activite": "", "conditions_paiement": "", "statut": "Actif", "date_creation_fiche": "", "commercial_referent": ""},
        ])
        result = deduplicate_clients(df, tlog)
        assert len(result) == 1
        assert result.iloc[0]["client_id"] == "C1"

    def test_returns_mapping_when_requested(self, tlog):
        df = pd.DataFrame([
            {"client_id": "C1", "raison_sociale": "Dupont SARL", "ville": "Tours", "email": "a@b.com", "siret": "12345678901234",
             "statut_juridique": "SARL", "adresse": "1 rue X", "code_postal": "37000", "telephone": "0247000000",
             "secteur_activite": "Industrie", "conditions_paiement": "30j", "statut": "Actif", "date_creation_fiche": "2024-01-01", "commercial_referent": "P. Martin"},
            {"client_id": "C2", "raison_sociale": "DUPONT", "ville": "", "email": "", "siret": "",
             "statut_juridique": "", "adresse": "", "code_postal": "", "telephone": "",
             "secteur_activite": "", "conditions_paiement": "", "statut": "Actif", "date_creation_fiche": "", "commercial_referent": ""},
        ])
        result, mapping = deduplicate_clients(df, tlog, return_mapping=True)
        assert len(result) == 1
        assert mapping == {"C2": "C1"}

    def test_remaps_dependent_client_references(self, tlog):
        df = pd.DataFrame([{
            "affaire_id": "A1",
            "client_id": "C2",
            "date_debut": "2024-01-01",
            "date_fin": "2024-12-31",
        }])
        result = remap_client_references(df, {"C2": "C1"}, tlog, "affaires", "affaire_id")
        assert result.iloc[0]["client_id"] == "C1"
        assert tlog.corrections[0]["rule"] == "client_reference_remap"

    def test_keeps_unique_records(self, tlog):
        df = pd.DataFrame([
            {"client_id": "C1", "raison_sociale": "Dupont SARL", "ville": "Tours", "email": "", "siret": "",
             "statut_juridique": "", "adresse": "", "code_postal": "", "telephone": "",
             "secteur_activite": "", "conditions_paiement": "", "statut": "Actif", "date_creation_fiche": "", "commercial_referent": ""},
            {"client_id": "C2", "raison_sociale": "Martin SAS", "ville": "Tours", "email": "", "siret": "",
             "statut_juridique": "", "adresse": "", "code_postal": "", "telephone": "",
             "secteur_activite": "", "conditions_paiement": "", "statut": "Actif", "date_creation_fiche": "", "commercial_referent": ""},
        ])
        result = deduplicate_clients(df, tlog)
        assert len(result) == 2


class TestTransformProduits:
    def test_negative_price_corrected(self, tlog):
        df = pd.DataFrame([{
            "produit_id": "P1", "designation": "Test", "description": "",
            "categorie": "A", "unite_vente": "pièce",
            "prix_unitaire_ht": "-10.5", "statut": "Actif",
            "code_ean": "", "date_derniere_maj": "2024-01-01",
        }])
        result = transform_produits(df, tlog)
        assert float(result.iloc[0]["prix_unitaire_ht"]) == 10.5
        assert tlog.count == 1


class TestTransformAffaires:
    def test_date_swap(self, tlog):
        df = pd.DataFrame([{
            "affaire_id": "A1", "client_id": "C1",
            "type_affaire": "Contrat", "objet": "Test",
            "date_debut": "2025-06-01", "date_fin": "2024-01-01",
            "montant_ht": "1000", "statut": "En cours",
            "commercial_referent": "", "date_creation": "2024-01-01",
        }])
        result = transform_affaires(df, {"C1"}, tlog)
        assert result.iloc[0]["date_debut"] == "2024-01-01"
        assert result.iloc[0]["date_fin"] == "2025-06-01"

    def test_date_swap_uses_parsed_dates(self, tlog):
        df = pd.DataFrame([{
            "affaire_id": "A1", "client_id": "C1",
            "type_affaire": "Contrat", "objet": "Test",
            "date_debut": "01/06/2025", "date_fin": "01/01/2024",
            "montant_ht": "1000", "statut": "En cours",
            "commercial_referent": "", "date_creation": "2024-01-01",
        }])
        result = transform_affaires(df, {"C1"}, tlog)
        assert result.iloc[0]["date_debut"] == "01/01/2024"
        assert result.iloc[0]["date_fin"] == "01/06/2025"

    def test_orphan_removed(self, tlog):
        df = pd.DataFrame([{
            "affaire_id": "A1", "client_id": "C999",
            "type_affaire": "Contrat", "objet": "Test",
            "date_debut": "2024-01-01", "date_fin": "2025-01-01",
            "montant_ht": "1000", "statut": "En cours",
            "commercial_referent": "", "date_creation": "2024-01-01",
        }])
        result = transform_affaires(df, {"C1", "C2"}, tlog)
        assert len(result) == 0


class TestTransformTarifs:
    def test_negative_price_fixed(self, tlog):
        df = pd.DataFrame([{
            "tarif_id": "T1", "produit_id": "P1", "client_id": "C1",
            "prix_unitaire_ht": "-8.50", "remise_pct": "0",
            "date_debut_validite": "2024-01-01", "date_fin_validite": "2025-01-01",
            "devise": "EUR", "conditions": "",
        }])
        result = transform_tarifs(df, {"C1"}, {"P1"}, tlog)
        assert float(result.iloc[0]["prix_unitaire_ht"]) == 8.50

    def test_orphan_produit_removed(self, tlog):
        df = pd.DataFrame([{
            "tarif_id": "T1", "produit_id": "P999", "client_id": "C1",
            "prix_unitaire_ht": "10", "remise_pct": "0",
            "date_debut_validite": "2024-01-01", "date_fin_validite": "2025-01-01",
            "devise": "EUR", "conditions": "",
        }])
        result = transform_tarifs(df, {"C1"}, {"P1"}, tlog)
        assert len(result) == 0

    def test_duplicate_tarifs_keep_latest_start_date(self, tlog):
        df = pd.DataFrame([
            {
                "tarif_id": "T1", "produit_id": "P1", "client_id": "C1",
                "prix_unitaire_ht": "10", "remise_pct": "0",
                "date_debut_validite": "2024-01-01", "date_fin_validite": "2024-12-31",
                "devise": "EUR", "conditions": "",
            },
            {
                "tarif_id": "T2", "produit_id": "P1", "client_id": "C1",
                "prix_unitaire_ht": "12", "remise_pct": "0",
                "date_debut_validite": "2025-01-01", "date_fin_validite": "2025-12-31",
                "devise": "EUR", "conditions": "",
            },
        ])
        result = transform_tarifs(df, {"C1"}, {"P1"}, tlog)
        assert len(result) == 1
        assert result.iloc[0]["tarif_id"] == "T2"
        assert any(c["rule"] == "tariff_duplicate_resolution" for c in tlog.corrections)
