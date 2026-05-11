"""Génération des graphiques Plotly pour le rapport."""

from __future__ import annotations

import plotly.graph_objects as go

from .config import COLORS
from .models import DomainReport, QualityIssue


def _fig_defaults(fig: go.Figure) -> go.Figure:
    """Applique le style commun à toutes les figures."""
    fig.update_layout(
        font=dict(family="Segoe UI, Arial, sans-serif", color=COLORS["text"]),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
    )
    return fig


def score_gauges(reports: list[DomainReport]) -> str:
    """Jauges de score qualité par domaine."""
    fig = go.Figure()
    n = len(reports)
    for i, r in enumerate(reports):
        score = r.quality_score
        color = (
            COLORS["ok"] if score >= 80
            else COLORS["majeur"] if score >= 60
            else COLORS["critique"]
        )
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": r.domain, "font": {"size": 16}},
            number={"suffix": "%", "font": {"size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "#ecf0f1",
                "steps": [
                    {"range": [0, 60], "color": "#fadbd8"},
                    {"range": [60, 80], "color": "#fdebd0"},
                    {"range": [80, 100], "color": "#d5f5e3"},
                ],
                "threshold": {
                    "line": {"color": COLORS["text"], "width": 2},
                    "thickness": 0.8,
                    "value": score,
                },
            },
            domain={"row": 0, "column": i},
        ))

    fig.update_layout(
        grid={"rows": 1, "columns": n, "pattern": "independent"},
        height=280,
        margin=dict(l=30, r=30, t=30, b=10),
    )
    return _fig_defaults(fig).to_html(full_html=False, include_plotlyjs=False)


def issues_by_domain(reports: list[DomainReport]) -> str:
    """Barres empilées : nombre d'anomalies par domaine et sévérité."""
    domains = [r.domain for r in reports]

    fig = go.Figure()
    for sev in ["critique", "majeur", "mineur"]:
        counts = []
        for r in reports:
            counts.append(sum(i.count for i in r.issues if i.severity == sev))
        fig.add_trace(go.Bar(
            name=sev.capitalize(),
            x=domains,
            y=counts,
            marker_color=COLORS[sev],
        ))

    fig.update_layout(
        barmode="stack",
        title="Anomalies détectées par domaine",
        yaxis_title="Nombre d'anomalies",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=50, b=60),
        height=380,
    )
    return _fig_defaults(fig).to_html(full_html=False, include_plotlyjs=False)


def completeness_chart(report: DomainReport) -> str:
    """Barres horizontales : taux de complétude par champ pour un domaine."""
    if not report.completeness:
        return ""

    fields = list(report.completeness.keys())
    values = list(report.completeness.values())
    bar_colors = [
        COLORS["ok"] if v >= 95
        else COLORS["majeur"] if v >= 80
        else COLORS["critique"]
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=fields,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v}%" for v in values],
        textposition="auto",
    ))
    fig.update_layout(
        title=f"Complétude des champs -{report.domain}",
        xaxis=dict(range=[0, 105], title="% renseigné"),
        height=max(250, len(fields) * 32 + 80),
    )
    return _fig_defaults(fig).to_html(full_html=False, include_plotlyjs=False)


def cross_table_summary(issues: list[QualityIssue]) -> str:
    """Barres : anomalies de cohérence inter-tables."""
    if not issues:
        return ""

    labels = [i.description.split(",")[0].strip() for i in issues]
    counts = [i.count for i in issues]
    colors = [COLORS[i.severity] for i in issues]

    fig = go.Figure(go.Bar(
        x=counts,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=counts,
        textposition="auto",
    ))
    fig.update_layout(
        title="Anomalies de cohérence inter-tables",
        xaxis_title="Nombre de lignes affectées",
        height=max(250, len(labels) * 45 + 80),
    )
    return _fig_defaults(fig).to_html(full_html=False, include_plotlyjs=False)


def category_breakdown(reports: list[DomainReport], cross_issues: list[QualityIssue]) -> str:
    """Répartition par catégorie de contrôle (Complétude, Validité, Unicité, Cohérence)."""
    categories = ["Complétude", "Validité", "Unicité", "Cohérence"]
    counts = []
    for cat in categories:
        total = sum(
            i.count for r in reports for i in r.issues if i.category == cat
        )
        if cat == "Cohérence":
            total += sum(i.count for i in cross_issues)
        counts.append(total)

    cat_colors = [COLORS["accent"], COLORS["majeur"], COLORS["critique"], COLORS["secondary"]]

    fig = go.Figure(go.Pie(
        labels=categories,
        values=counts,
        marker=dict(colors=cat_colors),
        textinfo="label+value",
        textfont=dict(color="white", size=13),
        hole=0.4,
    ))
    fig.update_layout(
        title="Répartition des anomalies par catégorie",
        height=350,
    )
    return _fig_defaults(fig).to_html(full_html=False, include_plotlyjs=False)
