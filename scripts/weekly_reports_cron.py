"""
Weekly Automated Reports

Generates and emails weekly performance reports to clients.

Includes:
- Claims summary (submitted, accepted, rejected)
- Recovery statistics
- Success rate trends
- Upcoming deadlines
- Carrier performance breakdown

Schedule with:
- Windows: Task Scheduler -> Run weekly on Monday at 9:00 AM
- Linux: crontab -> 0 9 * * 1
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager
from src.notifications.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_weekly_report(client_email: str) -> Dict:
    """Generate weekly performance report for a client."""
    
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get client
    cursor.execute("SELECT id, company_name FROM clients WHERE email = ?", (client_email,))
    client = cursor.fetchone()
    
    if not client:
        return None
    
    client_id, company_name = client
    
    # Get data for last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    
    # Claims submitted this week
    cursor.execute("""
        SELECT COUNT(*) FROM claims
        WHERE client_id = ? AND submitted_at >= ?
    """, (client_id, week_ago))
    claims_submitted = cursor.fetchone()[0]
    
    # Claims accepted this week
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(accepted_amount), 0)
        FROM claims
        WHERE client_id = ? 
        AND status = 'accepted'
        AND response_received_at >= ?
    """, (client_id, week_ago))
    accepted_count, accepted_amount = cursor.fetchone()
    
    # Claims rejected this week
    cursor.execute("""
        SELECT COUNT(*) FROM claims
        WHERE client_id = ? 
        AND status = 'rejected'
        AND response_received_at >= ?
    """, (client_id, week_ago))
    rejected_count = cursor.fetchone()[0]
    
    # Total pending claims
    cursor.execute("""
        SELECT COUNT(*) FROM claims
        WHERE client_id = ? AND status IN ('pending', 'submitted')
    """, (client_id,))
    pending_count = cursor.fetchone()[0]
    
    # Upcoming deadlines (next 7 days)
    next_week = datetime.now() + timedelta(days=7)
    cursor.execute("""
        SELECT COUNT(*), MIN(response_deadline)
        FROM claims
        WHERE client_id = ? 
        AND status IN ('pending', 'submitted')
        AND response_deadline BETWEEN ? AND ?
    """, (client_id, datetime.now(), next_week))
    upcoming_deadlines = cursor.fetchone()
    deadline_count, next_deadline = upcoming_deadlines
    
    # Carrier breakdown
    cursor.execute("""
        SELECT carrier, COUNT(*), 
               SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
               SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
        FROM claims
        WHERE client_id = ?
        AND created_at >= ?
        GROUP BY carrier
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """, (client_id, week_ago))
    carrier_stats = cursor.fetchall()
    
    conn.close()
    
    # Calculate success rate
    total_resolved = accepted_count + rejected_count
    success_rate = int((accepted_count / total_resolved * 100)) if total_resolved > 0 else 0
    
    # Calculate client share (80%)
    client_amount = round(accepted_amount * 0.8, 2) if accepted_amount else 0
    
    report = {
        'client_email': client_email,
        'company_name': company_name,
        'period_start': week_ago.strftime('%d/%m/%Y'),
        'period_end': datetime.now().strftime('%d/%m/%Y'),
        'claims_submitted': claims_submitted,
        'claims_accepted': accepted_count,
        'claims_rejected': rejected_count,
        'pending_claims': pending_count,
        'accepted_amount': accepted_amount,
        'client_amount': client_amount,
        'success_rate': success_rate,
        'upcoming_deadlines': deadline_count,
        'next_deadline': next_deadline.strftime('%d/%m/%Y') if next_deadline else 'N/A',
        'carrier_stats': carrier_stats
    }
    
    return report


def send_weekly_report(client_email: str, report: Dict) -> bool:
    """Send weekly report email to client."""
    
    try:
        # Build email HTML
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f8fafc; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 32px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; }}
        .content {{ padding: 32px 24px; }}
        .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }}
        .metric {{ background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: 700; color: #667eea; margin: 8px 0; }}
        .metric-label {{ font-size: 14px; color: #64748b; }}
        .section {{ margin: 24px 0; }}
        .section h2 {{ font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 12px; }}
        .carrier-row {{ padding: 12px; background: #f8fafc; margin: 8px 0; border-radius: 6px; display: flex; justify-content: space-between; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0; }}
        .footer {{ background: #f8fafc; padding: 24px; text-align: center; color: #64748b; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Rapport Hebdomadaire</h1>
            <p>{report['company_name']}</p>
            <p>{report['period_start']} - {report['period_end']}</p>
        </div>
        
        <div class="content">
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-label">Soumis cette semaine</div>
                    <div class="metric-value">{report['claims_submitted']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Acceptés</div>
                    <div class="metric-value" style="color: #10b981;">{report['claims_accepted']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Montant récupéré</div>
                    <div class="metric-value">{report['accepted_amount']:.2f}€</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Votre part (80%)</div>
                    <div class="metric-value" style="color: #667eea;">{report['client_amount']:.2f}€</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Performance</h2>
                <p><strong>Taux de succès:</strong> {report['success_rate']}%</p>
                <p><strong>Litiges en cours:</strong> {report['pending_claims']}</p>
                <p><strong>Deadlines à venir (7 jours):</strong> {report['upcoming_deadlines']}</p>
                {f"<p><strong>Prochaine deadline:</strong> {report['next_deadline']}</p>" if report['next_deadline'] != 'N/A' else ''}
            </div>
            
            <div class="section">
                <h2>📦 Transporteurs</h2>
                {''.join([f'''
                <div class="carrier-row">
                    <strong>{carrier}</strong>
                    <span>✅ {accepted} | ❌ {rejected} | Total: {total}</span>
                </div>
                ''' for carrier, total, accepted, rejected in report.get('carrier_stats', [])])}
            </div>
            
            <a href="https://dashboard.refundly.ai" class="button">Voir le dashboard complet</a>
        </div>
        
        <div class="footer">
            <p>© 2026 Refundly.ai - Automatisation des réclamations</p>
            <p>Vous recevez cet email car vous êtes client Refundly.ai</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Send email
        email_sender = EmailSender()
        success = email_sender.send_email(
            to_email=client_email,
            subject=f"📊 Rapport hebdomadaire - {report['company_name']}",
            html_content=html_body
        )
        
        if success:
            logger.info(f"✅ Weekly report sent to {client_email}")
        else:
            logger.warning(f"⚠️ Failed to send report to {client_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send weekly report to {client_email}: {e}")
        return False


def generate_and_send_all_reports():
    """Generate and send weekly reports to all active clients."""
    
    logger.info("=" * 70)
    logger.info("WEEKLY REPORTS GENERATOR - Starting")
    logger.info("=" * 70)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all active clients with at least one claim
        cursor.execute("""
            SELECT DISTINCT c.email, c.company_name
            FROM clients c
            JOIN claims cl ON c.id = cl.client_id
            WHERE c.email IS NOT NULL
        """)
        
        clients = cursor.fetchall()
        conn.close()
        
        logger.info(f"Generating reports for {len(clients)} clients...")
        
        sent_count = 0
        
        for client_email, company_name in clients:
            try:
                logger.info(f"Generating report for {company_name} ({client_email})")
                report = generate_weekly_report(client_email)
                
                if report:
                    if send_weekly_report(client_email, report):
                        sent_count += 1
                else:
                    logger.warning(f"No report data for {client_email}")
                    
            except Exception as e:
                logger.error(f"Failed to process {client_email}: {e}")
        
        logger.info("=" * 70)
        logger.info(f"COMPLETE: {sent_count}/{len(clients)} reports sent")
        logger.info("=" * 70)
        
        return sent_count
        
    except Exception as e:
        logger.error(f"❌ Reports generation failed: {e}")
        return 0


if __name__ == "__main__":
    print("\n📊 Weekly Reports Generator - Starting...\n")
    
    count = generate_and_send_all_reports()
    
    print(f"\n✅ Done! {count} reports sent.\n")
    
    sys.exit(0)
