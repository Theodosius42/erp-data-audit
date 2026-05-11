"""Point d'entrée : python -m analyse_qualite"""

from .loader import load_all
from .report import generate
from .validators import run_all_checks


def main() -> None:
    print("Chargement des données ERP...")
    data = load_all()
    for name, df in data.items():
        print(f"  {name}: {len(df)} lignes, {len(df.columns)} colonnes")

    print("\nExécution des contrôles qualité...")
    reports, cross_issues = run_all_checks(data)

    for r in reports:
        print(f"  {r.domain}: {r.total_issues} anomalies (score {r.quality_score}%)")
    print(f"  Cohérence inter-tables: {sum(i.count for i in cross_issues)} anomalies")

    print("\nGénération du rapport HTML...")
    output_path = generate(reports, cross_issues)
    print(f"\nRapport généré : {output_path}")


if __name__ == "__main__":
    main()
