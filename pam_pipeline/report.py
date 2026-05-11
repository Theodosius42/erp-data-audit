from datetime import date

from analyse_qualite.models import DomainReport, QualityIssue

from .config import REPORT_PATH


CSS = """
body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f8fb; color: #243447; }
header { background: #123c69; color: white; padding: 28px 40px; }
main { max-width: 1100px; margin: 0 auto; padding: 24px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; }
.card { background: white; border-radius: 8px; padding: 18px; box-shadow: 0 1px 6px rgba(0,0,0,.08); }
.value { font-size: 2rem; font-weight: 700; color: #123c69; }
table { width: 100%; border-collapse: collapse; background: white; margin-top: 14px; }
th, td { padding: 10px 12px; border-bottom: 1px solid #e8edf3; text-align: left; }
th { background: #123c69; color: white; }
.critique { color: #c0392b; font-weight: 700; }
.majeur { color: #b9770e; font-weight: 700; }
.mineur { color: #2471a3; font-weight: 700; }
"""


def _count(reports: list[DomainReport], cross_issues: list[QualityIssue]) -> int:
    return sum(r.total_issues for r in reports) + sum(i.count for i in cross_issues)


def _issue_rows(issues: list[QualityIssue]) -> str:
    severity_order = {"critique": 0, "majeur": 1, "mineur": 2}
    rows = []
    for issue in sorted(issues, key=lambda i: severity_order.get(i.severity, 3)):
        sample = ", ".join(issue.affected_ids[:6])
        rows.append(
            f"<tr><td class='{issue.severity}'>{issue.severity}</td><td>{issue.domain}</td>"
            f"<td>{issue.category}</td><td><code>{issue.field}</code></td>"
            f"<td>{issue.description}</td><td>{issue.count}</td><td>{sample}</td></tr>"
        )
    return "\n".join(rows) if rows else "<tr><td colspan='7'>Aucune anomalie.</td></tr>"


def generate(pre_reports: list[DomainReport], pre_cross: list[QualityIssue], post_reports: list[DomainReport], post_cross: list[QualityIssue], corrections_count: int) -> str:
    pre_total = _count(pre_reports, pre_cross)
    post_total = _count(post_reports, post_cross)
    all_post = [i for r in post_reports for i in r.issues] + post_cross
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Audit Qualité PAM</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <h1>Audit Qualité PAM</h1>
    <p>Réservations, inscriptions, trajets et régulation - {date.today().strftime("%d/%m/%Y")}</p>
  </header>
  <main>
    <section class="grid">
      <div class="card"><div class="value">{pre_total}</div><div>Anomalies source</div></div>
      <div class="card"><div class="value">{corrections_count}</div><div>Corrections appliquées</div></div>
      <div class="card"><div class="value">{post_total}</div><div>Anomalies restantes</div></div>
      <div class="card"><div class="value">{sum(i.count for i in all_post if i.severity == "critique")}</div><div>Lignes critiques restantes</div></div>
    </section>
    <section>
      <h2>Scores post-transformation</h2>
      <table>
        <thead><tr><th>Domaine</th><th>Lignes</th><th>Anomalies</th><th>Score</th></tr></thead>
        <tbody>
          {''.join(f'<tr><td>{r.domain}</td><td>{r.total_rows}</td><td>{r.total_issues}</td><td>{r.quality_score}%</td></tr>' for r in post_reports)}
        </tbody>
      </table>
    </section>
    <section>
      <h2>Anomalies post-transformation</h2>
      <table>
        <thead><tr><th>Sévérité</th><th>Domaine</th><th>Catégorie</th><th>Champ</th><th>Description</th><th>Nb</th><th>Exemples</th></tr></thead>
        <tbody>{_issue_rows(all_post)}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"""
    REPORT_PATH.write_text(html, encoding="utf-8")
    return str(REPORT_PATH)
