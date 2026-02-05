"""
Auto Recovery Orchestrator - Coordinates the complete automated recovery process.

This orchestrator manages the end-to-end workflow from dispute detection
to automatic claim submission and tracking.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from ai.pod_analyzer import PODAnalyzer
from ai.claim_generator import ClaimGenerator
from ai.skill_executor import AntigravitySkillExecutor
from auth.credentials_manager import CredentialsManager

logger = logging.getLogger(__name__)


class AutoRecoveryOrchestrator:
    """Orchestrate the complete automated recovery workflow."""
    
    def __init__(self, openai_api_key: Optional[str] = None, db_manager=None):
        """
        Initialize orchestrator.
        
        Args:
            openai_api_key: OpenAI API key for Vision AI (optional)
            db_manager: Database manager instance (optional, for tests)
        """
        self.pod_analyzer = None
        if openai_api_key:
            try:
                self.pod_analyzer = PODAnalyzer(api_key=openai_api_key)
                logger.info("POD Analyzer initialized")
            except ImportError as e:
                logger.warning(f"POD Analyzer not available: {e}")
        
        self.claim_generator = ClaimGenerator()
        self.credentials_manager = CredentialsManager()
        self.skill_executor = AntigravitySkillExecutor()  # NEW: Antigravity integration
        
        # Database management
        if db_manager:
            self.db = db_manager
        else:
            from src.database import get_db_manager
            self.db = get_db_manager()
        
        logger.info("AutoRecoveryOrchestrator initialized with Antigravity skills")
    
    async def process_dispute(self, dispute: Dict) -> Dict:
        """
        Process a single dispute through complete recovery workflow.
        
        Workflow:
        1. Analyze POD if available (Vision AI)
        2. Generate claim text
        3. Submit claim (API or portal)
        4. Track status
        5. Update dashboard
        6. Notify client
        
        Args:
            dispute: Dispute dictionary with all details
            
        Returns:
            Result dictionary with status and details
        """
        logger.info(f"Processing dispute: {dispute.get('order_id', 'N/A')}")
        
        result = {
            'dispute_id': dispute.get('order_id'),
            'started_at': datetime.now().isoformat(),
            'steps_completed': [],
            'success': False
        }
        
        try:
            # Step 1: Analyze POD if available
            pod_analysis = None
            if dispute.get('pod_image_path') and self.pod_analyzer:
                logger.info("Step 1: Analyzing POD with Vision AI...")
                pod_analysis = await self._analyze_pod(dispute)
                result['steps_completed'].append('pod_analysis')
                result['pod_analysis'] = pod_analysis
            
            # Step 2: Generate claim
            logger.info("Step 2: Generating claim text...")
            claim_text = self.claim_generator.generate(dispute, pod_analysis)
            result['steps_completed'].append('claim_generation')
            result['claim_text'] = claim_text
            
            # Save claim to file
            claim_path = Path(f"data/claims/{dispute.get('order_id', 'unknown')}_claim.txt")
            self.claim_generator.save_claim(claim_text, str(claim_path))
            result['claim_file'] = str(claim_path)
            
            # Step 3: Submit claim
            logger.info("Step 3: Submitting claim...")
            submission_result = await self._submit_claim(dispute, claim_text, pod_analysis)
            result['steps_completed'].append('claim_submission')
            result['submission'] = submission_result
            
            # Step 4: Track status (placeholder for now)
            logger.info("Step 4: Setting up tracking...")
            result['steps_completed'].append('tracking_setup')
            result['tracking_id'] = submission_result.get('tracking_id', 'pending')
            
            # Step 5: Update dashboard
            logger.info("Step 5: Updating client dashboard...")
            await self._update_dashboard(dispute, result)
            result['steps_completed'].append('dashboard_update')
            
            # Step 6: Notify client
            logger.info("Step 6: Sending notification...")
            await self._notify_client(dispute, result)
            result['steps_completed'].append('client_notification')
            
            result['success'] = True
            result['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Dispute processed successfully: {dispute.get('order_id')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing dispute: {e}")
            result['error'] = str(e)
            result['failed_at'] = datetime.now().isoformat()
        
        return result
    
    async def _analyze_pod(self, dispute: Dict) -> Optional[Dict]:
        """Analyze POD image using Vision AI."""
        pod_path = dispute.get('pod_image_path')
        
        if not pod_path or not self.pod_analyzer:
            return None
        
        try:
            # Run POD analysis (sync function, but wrapped in async)
            analysis = await asyncio.to_thread(
                self.pod_analyzer.analyze_pod_image,
                pod_path,
                tracking_number=dispute.get('tracking_number'),
                expected_delivery_date=dispute.get('expected_delivery_date')
            )
            
            logger.info(f"POD analyzed. Confidence invalid: {analysis.get('confidence_invalid', 0):.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"POD analysis failed: {e}")
            return {'error': str(e)}
    
    async def _submit_claim(
        self, 
        dispute: Dict,
        claim_text: str,
        pod_analysis: Optional[Dict]
    ) -> Dict:
        """
        Submit claim via API or portal.
        
        Saves initially as 'pending' in database, then attempts submission.
        """
        carrier = dispute.get('carrier', '').lower()
        
        try:
            db = self.db
            
            # Step 1: Create initial claim record in database
            # Get client
            client = db.get_client(email=dispute.get('client_email'))
            
            if not client:
                logger.error(f"Client not found: {dispute.get('client_email')}")
                # Fallback to creating a guest client or using generic ID if possible
                client_id = 0  # Should be handled better in production
            else:
                client_id = client['id']
            
            # Generate local reference if not already provided
            import random
            import string
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            claim_ref = f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{suffix}-{carrier[:3].upper()}"
            
            claim_id = db.create_claim(
                claim_reference=claim_ref,
                client_id=client_id,
                order_id=dispute.get('order_id'),
                carrier=carrier,
                dispute_type=dispute.get('dispute_type'),
                amount_requested=dispute.get('total_recoverable', 0.0),
                tracking_number=dispute.get('tracking_number'),
                order_date=dispute.get('order_date')
            )
            
            # Send notification email for claim creation
            try:
                from src.notifications.notification_manager import NotificationManager
                notification_mgr = NotificationManager()
                notification_mgr.queue_notification(
                    client_email=dispute.get('client_email'),
                    event_type='claim_created',
                    context={
                        'claim_ref': claim_ref,
                        'carrier': carrier.capitalize(),
                        'amount': dispute.get('total_recoverable', 0.0)
                    }
                )
                logger.info(f"📧 Notification queued for claim creation: {claim_ref}")
            except Exception as e:
                logger.warning(f"Failed to queue notification: {e}")
            
            # Auto-fetch POD (hybrid approach: try auto, fallback to manual)
            if dispute.get('tracking_number'):
                try:
                    from src.integrations.pod_fetcher import PODFetcher
                    pod_fetcher = PODFetcher()
                    
                    logger.info(f"🔍 Attempting POD auto-fetch for {claim_ref}...")
                    pod_result = pod_fetcher.fetch_pod(
                        tracking_number=dispute['tracking_number'],
                        carrier=carrier
                    )
                    
                    if pod_result['success']:
                        # Update claim with auto-fetched POD
                        db.update_claim(
                            claim_id,
                            pod_url=pod_result['pod_url'],
                            pod_fetch_status='success',
                            pod_fetched_at=datetime.now(),
                            pod_delivery_person=pod_result['pod_data'].get('recipient_name')
                        )
                        logger.info(f"✅ POD auto-fetched successfully for {claim_ref}")
                    else:
                        # Log failure, user can upload manually
                        db.update_claim(
                            claim_id,
                            pod_fetch_status='failed',
                            pod_fetch_error=pod_result['error']
                        )
                        logger.warning(f"⚠️ POD auto-fetch failed: {pod_result['error']} - Manual upload available")
                        
                except Exception as e:
                    logger.error(f"POD auto-fetch exception: {e}")
                    db.update_claim(claim_id, pod_fetch_status='failed', pod_fetch_error=str(e))
            
            
            # Step 2: Attempt submission
            submission_result = {}
            
            # Check if we have API access
            if self._has_api_access(carrier):
                submission_result = await self._submit_via_api(dispute, claim_text, claim_id, claim_ref)
            else:
                submission_result = await self._submit_via_portal(dispute, claim_text, pod_analysis)
            
            # Step 3: Update database with submission results
            status = 'submitted' if submission_result.get('status') in ['submitted', 'success', 'success_simulated'] else 'pending_manual'
            
            db.update_claim(
                claim_id=claim_id,
                status=status,
                submitted_at=datetime.now() if status == 'submitted' else None,
                automation_status='automated' if status == 'submitted' else 'manual_intervention_required',
                skill_used='api' if self._has_api_access(carrier) else 'portal'
            )
            
            # Enrich result with database ID
            submission_result['claim_id'] = claim_id
            if 'claim_reference' not in submission_result:
                submission_result['claim_reference'] = claim_ref
                
            return submission_result
            
        except Exception as e:
            logger.error(f"Error in _submit_claim: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'method': 'unknown'
            }
    
    def _has_api_access(self, carrier: str) -> bool:
        """Check if carrier has API integration."""
        # For now, most carriers don't have claim submission APIs
        # This would be extended based on actual carrier APIs
        api_carriers = []  # Empty for now
        
        return carrier in api_carriers
    
    async def _submit_via_api(self, dispute: Dict, claim_text: str, claim_id: int, claim_ref: str) -> Dict:
        """Submit claim via carrier API."""
        logger.info("Submitting via API...")
        
        # Implement actual API submission
        carrier = dispute.get('carrier', '').lower()
        
        try:
            # Here we would do the actual API call
            # For now, it's a simulated success
            
            logger.info(f"✅ Claim {claim_ref} submitted via API (Simulated)")
            
            return {
                'method': 'api',
                'status': 'submitted',
                'claim_reference': claim_ref,
                'claim_id': claim_id,
                'submitted_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"API submission failed: {e}")
            return {
                'method': 'api',
                'status': 'failed',
                'error': str(e),
                'submitted_at': datetime.now().isoformat()
            }
    
    async def _submit_via_portal(
        self,
        dispute: Dict,
        claim_text: str,
        pod_analysis: Optional[Dict]
    ) -> Dict:
        """
        Submit claim via web portal using Antigravity skills.
        
        This uses the SkillExecutor to navigate carrier portals automatically.
        """
        carrier = dispute.get('carrier', '').lower()
        
        logger.info(f"Attempting portal submission for {carrier}...")
        
        # Check if we have an Antigravity skill for this carrier
        if self.skill_executor.can_handle(carrier):
            logger.info(f"✓ Using Antigravity skill for {carrier}")
            
            return await self.skill_executor.execute_claim_submission(
                carrier=carrier,
                dispute=dispute,
                claim_text=claim_text,
                pod_analysis=pod_analysis
            )
        else:
            # No automation available
            logger.warning(f"✗ No Antigravity skill available for {carrier}")
            
            return {
                'method': 'manual_required',
                'carrier': carrier,
                'status': 'pending_manual',
                'message': f'No automation available for {carrier}. Manual submission required.',
                'tracking_id': f"MANUAL-{dispute.get('tracking_number', 'unknown')}",
                'submitted_at': datetime.now().isoformat(),
                'action_required': 'Create manual task ticket for human operator'
            }
            # Automatisation de la création de ticket manuel et notification
            try:
                from src.notifications.task_manager import create_manual_task, notify_operator
                task_id = create_manual_task(
                    task_type='manual_claim_submission',
                    claim_reference=dispute.get('claim_reference'),
                    carrier=dispute.get('carrier'),
                    reason='Automation fallback',
                    priority='high'
                )
                notify_operator(task_id=task_id, message=f"Intervention requise pour la réclamation {dispute.get('claim_reference')}")
                logger.info(f"📝 Ticket manuel créé et opérateur notifié (task_id={task_id})")
            except Exception as e:
                logger.error(f"Erreur lors de la création du ticket manuel ou notification opérateur: {e}")
    
    async def _update_dashboard(self, dispute: Dict, result: Dict):
        """Update client dashboard with claim status."""
        try:
            db = self.db
            
            # Get claim_id from submission result
            submission = result.get('submission', {})
            claim_id = submission.get('claim_id')
            
            if claim_id:
                # Update claim with latest status
                db.update_claim(
                    claim_id=claim_id,
                    automation_status='completed',
                    updated_at=datetime.now()
                )
                
                logger.info(f"✅ Dashboard updated: Claim #{claim_id} status updated")
            else:
                logger.warning("No claim_id found in submission result")
                
        except Exception as e:
            logger.error(f"Dashboard update failed: {e}")
    
    async def _notify_client(self, dispute: Dict, result: Dict):
        """Send notification to client about claim submission."""
        try:
            from src.email_service import send_claim_submitted_email
            db = self.db
            client_email = dispute.get('client_email')
            submission = result.get('submission', {})
            
            if client_email and submission:
                send_claim_submitted_email(
                    client_email=client_email,
                    claim_reference=submission.get('claim_reference', 'N/A'),
                    carrier=dispute.get('carrier'),
                    amount_requested=dispute.get('total_recoverable'),
                    order_id=dispute.get('order_id'),
                    submission_method=submission.get('method')
                )
                
                # Log notification
                db = self.db
                client = db.get_client(email=client_email)
                if client:
                    db.log_notification(
                        client_id=client['id'],
                        notification_type='claim_submitted',
                        subject=f"Réclamation {submission.get('claim_reference')} soumise",
                        sent_to=client_email,
                        status='sent',
                        related_claim_id=submission.get('claim_id')
                    )
                
                logger.info(f"📧 Notification sent to {client_email}")
            else:
                logger.warning("Missing client_email or submission data for notification")
                
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
    
    async def process_batch(self, disputes: List[Dict]) -> List[Dict]:
        """
        Process multiple disputes in batch.
        
        Args:
            disputes: List of dispute dictionaries
            
        Returns:
            List of results
        """
        logger.info(f"Processing batch of {len(disputes)} disputes...")
        
        tasks = [self.process_dispute(d) for d in disputes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        
        logger.info(f"Batch complete: {successful}/{len(disputes)} successful")
        
        return results


# Demo/Test script
async def main():
    """Demo of auto recovery orchestrator."""
    import os
    
    print("="*70)
    print("AUTO RECOVERY ORCHESTRATOR - Demo")
    print("="*70)
    
    # Initialize (with or without OpenAI key)
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        print("\n✅ OpenAI API key found - POD analysis enabled")
    else:
        print("\n⚠️  No OpenAI API key - POD analysis disabled")
        print("   Set OPENAI_API_KEY environment variable to enable")
    
    orchestrator = AutoRecoveryOrchestrator(openai_api_key=api_key)
    
    # Example dispute
    dispute = {
        'order_id': 'ORD-12345',
        'tracking_number': 'FR987654321',
        'carrier': 'colissimo',
        'dispute_type': 'pod_invalide',
        'order_date': '2024-01-10',
        'delivery_date': '2024-01-15',
        'order_value': 150.00,
        'shipping_cost': 12.50,
        'total_recoverable': 182.50,
        'client_name': 'Jean Dupont',
        'client_email': 'jean.dupont@example.com',
        'recipient_name': 'Marie Martin',
        # 'pod_image_path': 'path/to/pod.jpg'  # Uncomment if you have a real POD
    }
    
    print("\n" + "-"*70)
    print("Processing dispute...")
    print(f"Order ID: {dispute['order_id']}")
    print(f"Carrier: {dispute['carrier']}")
    print(f"Type: {dispute['dispute_type']}")
    print(f"Amount: {dispute['total_recoverable']}€")
    print("-"*70)
    
    # Process
    result = await orchestrator.process_dispute(dispute)
    
    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Steps completed: {', '.join(result['steps_completed'])}")
    
    if result.get('claim_file'):
        print(f"\n📄 Claim saved to: {result['claim_file']}")
    
    if result.get('submission'):
        sub = result['submission']
        print(f"\n📤 Submission:")
        print(f"   Method: {sub.get('method')}")
        print(f"   Status: {sub.get('status')}")
        print(f"   Tracking ID: {sub.get('tracking_id')}")
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
