"""Assemblage du rapport HTML."""

from __future__ import annotations

from datetime import date

from plotly.offline import get_plotlyjs

from . import charts
from .config import COLORS, OUTPUT_FILE, SEVERITY_ORDER
from .models import DomainReport, QualityIssue

CSS = """
:root {
    --primary: %(primary)s;
    --accent: %(accent)s;
    --bg: %(bg)s;
    --text: %(text)s;
    --critique: %(critique)s;
    --majeur: %(majeur)s;
    --mineur: %(mineur)s;
    --ok: %(ok)s;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--text);
    background: var(--bg);
    line-height: 1.6;
}
.container { max-width: 1100px; margin: 0 auto; padding: 20px; }
header {
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: white;
    padding: 40px 20px;
    text-align: center;
}
header h1 { font-size: 2em; margin-bottom: 8px; }
header p { opacity: 0.85; font-size: 1.1em; }
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 24px 0;
}
.kpi-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid var(--accent);
}
.kpi-card.critique { border-left-color: var(--critique); }
.kpi-card.majeur { border-left-color: var(--majeur); }
.kpi-card.ok { border-left-color: var(--ok); }
.kpi-value { font-size: 2.2em; font-weight: 700; color: var(--primary); }
.kpi-label { font-size: 0.9em; color: #7f8c8d; margin-top: 4px; }
section { margin: 32px 0; }
h2 {
    color: var(--primary);
    border-bottom: 2px solid var(--accent);
    padding-bottom: 8px;
    margin-bottom: 20px;
    font-size: 1.5em;
}
h3 { color: var(--primary); margin: 16px 0 8px 0; }
.chart-box {
    background: white;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.issues-table {
    width: 100%%;
    border-collapse: collapse;
    margin: 12px 0;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.issues-table th {
    background: var(--primary);
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}
.issues-table td { padding: 10px 14px; border-bottom: 1px solid #ecf0f1; }
.issues-table tr:hover { background: #f8f9fa; }
.severity {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 600;
    color: white;
}
.severity.critique { background: var(--critique); }
.severity.majeur { background: var(--majeur); }
.severity.mineur { background: var(--mineur); }
.sample-ids {
    font-family: 'Consolas', monospace;
    font-size: 0.82em;
    color: #7f8c8d;
}
.section-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
@media (max-width: 768px) { .section-grid { grid-template-columns: 1fr; } }
footer {
    text-align: center;
    color: #95a5a6;
    padding: 30px;
    font-size: 0.9em;
}
@media print {
    header { padding: 20px; }
    .chart-box { break-inside: avoid; }
    body { background: white; }
}
""" % COLORS


def _severity_badge(severity: str) -> str:
    return f'<span class="severity {severity}">{severity.capitalize()}</span>'


def _issues_table(issues: list[QualityIssue]) -> str:
    """Génère un tableau HTML pour une liste d'anomalies."""
    if not issues:
        return '<p style="color: #27ae60; font-weight: 600;">Aucune anomalie détectée.</p>'

    sorted_issues = sorted(issues, key=lambda i: SEVERITY_ORDER.index(i.severity))
    rows = ""
    for issue in sorted_issues:
        sample = ", ".join(issue.affected_ids[:5])
        if issue.count > 5:
            sample += f" ... (+{issue.count - 5})"
        rows += f"""<tr>
            <td>{_severity_badge(issue.severity)}</td>
            <td>{issue.category}</td>
            <td><code>{issue.field}</code></td>
            <td>{issue.description}</td>
            <td style="text-align:center;font-weight:700">{issue.count}</td>
            <td class="sample-ids">{sample}</td>
        </tr>"""

    return f"""<table class="issues-table">
        <thead><tr>
            <th>Sévérité</th><th>Catégorie</th><th>Champ</th>
            <th>Description</th><th>Nb</th><th>Exemples</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>"""


def generate(
    reports: list[DomainReport],
    cross_issues: list[QualityIssue],
) -> str:
    """Génère le rapport HTML complet et l'écrit sur disque."""
    total_rows = sum(r.total_rows for r in reports)
    total_issues = sum(r.total_issues for r in reports) + sum(i.count for i in cross_issues)
    total_critical = sum(r.critical_count for r in reports) + sum(
        i.count for i in cross_issues if i.severity == "critique"
    )
    avg_score = round(sum(r.quality_score for r in reports) / len(reports), 1)

    # --- KPI cards ---
    kpi_html = f"""
    <div class="kpi-grid">
        <div class="kpi-card ok">
            <div class="kpi-value">{avg_score}%</div>
            <div class="kpi-label">Score qualité global</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{total_rows}</div>
            <div class="kpi-label">Lignes analysées</div>
        </div>
        <div class="kpi-card majeur">
            <div class="kpi-value">{total_issues}</div>
            <div class="kpi-label">Anomalies détectées</div>
        </div>
        <div class="kpi-card critique">
            <div class="kpi-value">{total_critical}</div>
            <div class="kpi-label">Anomalies critiques</div>
        </div>
    </div>"""

    # --- Overview charts ---
    gauges_html = charts.score_gauges(reports)
    domain_bars_html = charts.issues_by_domain(reports)
    category_pie_html = charts.category_breakdown(reports, cross_issues)

    # --- Per-domain detail ---
    domain_sections = ""
    for report in reports:
        completeness_html = charts.completeness_chart(report)
        table_html = _issues_table(report.issues)
        domain_sections += f"""
        <section>
            <h3>{report.domain} ({report.total_rows} lignes -score {report.quality_score}%)</h3>
            <div class="chart-box">{completeness_html}</div>
            {table_html}
        </section>"""

    # --- Cross-table ---
    cross_chart_html = charts.cross_table_summary(cross_issues)
    cross_table_html = _issues_table(cross_issues)

    # --- Recommendations ---
    reco_items = _build_recommendations(reports, cross_issues)
    reco_html = "<ol>" + "".join(f"<li>{r}</li>" for r in reco_items) + "</ol>"

    plotly_js = get_plotlyjs()

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Audit Qualité Données ERP</title>
    <script>{plotly_js}</script>
    <style>{CSS}</style>
</head>
<body>
    <header>
        <h1>Audit Qualité des Données ERP</h1>
        <p>Rapport généré le {date.today().strftime("%d/%m/%Y")}
        -Simulation de migration ERP</p>
    </header>

    <div class="container">
        <section>
            <h2>1. Vue d'ensemble</h2>
            {kpi_html}
            <div class="chart-box">{gauges_html}</div>
            <div class="section-grid">
                <div class="chart-box">{domain_bars_html}</div>
                <div class="chart-box">{category_pie_html}</div>
            </div>
        </section>

        <section>
            <h2>2. Analyse détaillée par domaine</h2>
            {domain_sections}
        </section>

        <section>
            <h2>3. Cohérence inter-tables</h2>
            <div class="chart-box">{cross_chart_html}</div>
            {cross_table_html}
        </section>

        <section>
            <h2>4. Recommandations</h2>
            {reco_html}
        </section>
    </div>

    <footer>
        Audit réalisé par Tudor Haruța -{date.today().strftime("%d/%m/%Y")}
        <br>Données simulées pour démonstration de compétences en gestion de qualité de données ERP
    </footer>
</body>
</html>"""

    OUTPUT_FILE.write_text(html, encoding="utf-8")
    return str(OUTPUT_FILE)


def _build_recommendations(
    reports: list[DomainReport], cross_issues: list[QualityIssue]
) -> list[str]:
    """Génère des recommandations basées sur les anomalies trouvées."""
    recos: list[str] = []

    # Find most problematic areas
    all_issues = [i for r in reports for i in r.issues] + cross_issues
    critical = [i for i in all_issues if i.severity == "critique"]

    if any("doublon" in i.description.lower() for i in critical):
        recos.append(
            "<strong>Dédoublonnage clients :</strong> Mettre en place une procédure "
            "de fusion des fiches clients en doublon avant la migration. "
            "Définir une clé unique (SIRET + raison sociale normalisée)."
        )

    if any("orphan" in i.field or "inexistant" in i.description for i in all_issues):
        recos.append(
            "<strong>Intégrité référentielle :</strong> Corriger ou supprimer les "
            "références orphelines (affaires et tarifs pointant vers des clients/produits "
            "inexistants) avant l'import dans le nouveau système."
        )

    if any("siret" in i.field.lower() for i in all_issues):
        recos.append(
            "<strong>Validation SIRET :</strong> Compléter les SIRET manquants et "
            "corriger les formats invalides. Envisager une vérification via l'API "
            "Sirene de l'INSEE."
        )

    if any("date" in i.field.lower() and "postérieure" in i.description for i in all_issues):
        recos.append(
            "<strong>Cohérence des dates :</strong> Corriger les inversions "
            "date_debut/date_fin. Ajouter une contrainte de validation dans le "
            "nouveau ERP pour empêcher ces erreurs à la saisie."
        )

    if any("négatif" in i.description.lower() for i in all_issues):
        recos.append(
            "<strong>Prix négatifs :</strong> Identifier et corriger les prix "
            "négatifs dans les tarifs et produits. Mettre en place une règle de "
            "validation (prix ≥ 0) dans le nouveau système."
        )

    if any("ville" in i.field.lower() for i in all_issues):
        recos.append(
            "<strong>Standardisation des adresses :</strong> Normaliser les noms de "
            "villes selon le référentiel officiel. Utiliser un menu déroulant ou une "
            "API d'adresse (api-adresse.data.gouv.fr) dans le nouveau ERP."
        )

    recos.append(
        "<strong>Documentation des processus :</strong> Rédiger des guides de saisie "
        "utilisateur pour le nouveau ERP afin de prévenir la réapparition de ces "
        "anomalies."
    )

    return recos
