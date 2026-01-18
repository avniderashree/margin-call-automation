"""
Alert System Module
===================
Generates and manages alerts for margin-related events.

Features:
- Configurable alert thresholds
- Multiple alert channels (console, file, email placeholder)
- Alert severity levels
- Alert history and acknowledgment
"""

import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of alerts."""
    MARGIN_WARNING = "margin_warning"
    MARGIN_CALL = "margin_call"
    OVERDUE_CALL = "overdue_call"
    COLLATERAL_BREACH = "collateral_breach"
    CONCENTRATION_BREACH = "concentration_breach"
    PAYMENT_RECEIVED = "payment_received"
    CALL_SATISFIED = "call_satisfied"
    SYSTEM = "system"


@dataclass
class Alert:
    """
    Represents an alert.
    
    Attributes:
        alert_id: Unique identifier
        alert_type: Type of alert
        severity: Severity level
        message: Alert message
        timestamp: When the alert was created
        account_id: Related account
        data: Additional data
        is_acknowledged: Whether alert has been acknowledged
        acknowledged_by: Who acknowledged (if applicable)
        acknowledged_at: When acknowledged (if applicable)
    """
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    account_id: str = ""
    data: Optional[Dict] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'account_id': self.account_id,
            'data': self.data,
            'is_acknowledged': self.is_acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class AlertSystem:
    """
    Alert management system.
    
    Features:
    - Generate alerts based on margin events
    - Configurable thresholds
    - Alert acknowledgment
    - Alert history and filtering
    - Console and file output
    """
    
    def __init__(
        self,
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0,
        emergency_threshold: float = 110.0,
        log_to_file: bool = False,
        log_file_path: str = "output/alerts.log"
    ):
        """
        Initialize alert system.
        
        Parameters:
            warning_threshold: Utilization % for warning alerts
            critical_threshold: Utilization % for critical alerts
            emergency_threshold: Utilization % for emergency alerts
            log_to_file: Whether to write alerts to file
            log_file_path: Path to log file
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.emergency_threshold = emergency_threshold
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        
        self.alerts: Dict[str, Alert] = {}
        self._alert_counter = 0
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        return f"ALERT-{datetime.now().strftime('%Y%m%d')}-{self._alert_counter:05d}"
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        account_id: str = "",
        data: Optional[Dict] = None
    ) -> Alert:
        """
        Create and store an alert.
        
        Parameters:
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            account_id: Related account
            data: Additional data
        
        Returns:
            Created Alert object
        """
        alert_id = self._generate_alert_id()
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            account_id=account_id,
            data=data
        )
        
        self.alerts[alert_id] = alert
        self._output_alert(alert)
        
        return alert
    
    def _output_alert(self, alert: Alert) -> None:
        """Output alert to configured channels."""
        # Console output with color coding
        severity_colors = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.EMERGENCY: "🚨"
        }
        
        icon = severity_colors.get(alert.severity, "📢")
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{timestamp}] {icon} [{alert.severity.value.upper()}] "
              f"[{alert.alert_type.value}] {alert.message}")
        
        # File output if enabled
        if self.log_to_file:
            self._write_to_file(alert)
    
    def _write_to_file(self, alert: Alert) -> None:
        """Write alert to log file."""
        try:
            line = (
                f"{alert.timestamp.isoformat()}|"
                f"{alert.severity.value}|"
                f"{alert.alert_type.value}|"
                f"{alert.account_id}|"
                f"{alert.message}\n"
            )
            with open(self.log_file_path, 'a') as f:
                f.write(line)
        except IOError:
            pass  # Silently fail if file write fails
    
    def check_margin_utilization(
        self,
        account_id: str,
        utilization_pct: float
    ) -> Optional[Alert]:
        """
        Check margin utilization and create alert if needed.
        
        Parameters:
            account_id: Account identifier
            utilization_pct: Current utilization percentage
        
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        if utilization_pct >= self.emergency_threshold:
            return self.create_alert(
                alert_type=AlertType.MARGIN_WARNING,
                severity=AlertSeverity.EMERGENCY,
                message=f"EMERGENCY: Margin utilization at {utilization_pct:.1f}% "
                        f"(threshold: {self.emergency_threshold}%)",
                account_id=account_id,
                data={'utilization_pct': utilization_pct}
            )
        elif utilization_pct >= self.critical_threshold:
            return self.create_alert(
                alert_type=AlertType.MARGIN_WARNING,
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL: Margin utilization at {utilization_pct:.1f}% "
                        f"(threshold: {self.critical_threshold}%)",
                account_id=account_id,
                data={'utilization_pct': utilization_pct}
            )
        elif utilization_pct >= self.warning_threshold:
            return self.create_alert(
                alert_type=AlertType.MARGIN_WARNING,
                severity=AlertSeverity.WARNING,
                message=f"WARNING: Margin utilization at {utilization_pct:.1f}% "
                        f"(threshold: {self.warning_threshold}%)",
                account_id=account_id,
                data={'utilization_pct': utilization_pct}
            )
        
        return None
    
    def alert_margin_call(
        self,
        account_id: str,
        call_id: str,
        amount: float,
        due_date: datetime
    ) -> Alert:
        """
        Create margin call alert.
        
        Parameters:
            account_id: Account identifier
            call_id: Margin call ID
            amount: Call amount
            due_date: Due date
        
        Returns:
            Created alert
        """
        return self.create_alert(
            alert_type=AlertType.MARGIN_CALL,
            severity=AlertSeverity.CRITICAL,
            message=f"Margin call issued: ${amount:,.2f} due by {due_date.strftime('%Y-%m-%d %H:%M')}",
            account_id=account_id,
            data={'call_id': call_id, 'amount': amount, 'due_date': due_date.isoformat()}
        )
    
    def alert_overdue_call(
        self,
        account_id: str,
        call_id: str,
        amount: float,
        hours_overdue: float
    ) -> Alert:
        """
        Create overdue margin call alert.
        
        Parameters:
            account_id: Account identifier
            call_id: Margin call ID
            amount: Outstanding amount
            hours_overdue: Hours past due
        
        Returns:
            Created alert
        """
        return self.create_alert(
            alert_type=AlertType.OVERDUE_CALL,
            severity=AlertSeverity.EMERGENCY,
            message=f"OVERDUE: Margin call {call_id} of ${amount:,.2f} is {hours_overdue:.1f} hours past due",
            account_id=account_id,
            data={'call_id': call_id, 'amount': amount, 'hours_overdue': hours_overdue}
        )
    
    def alert_concentration_breach(
        self,
        account_id: str,
        breaches: List[str]
    ) -> Alert:
        """
        Create concentration breach alert.
        
        Parameters:
            account_id: Account identifier
            breaches: List of breach descriptions
        
        Returns:
            Created alert
        """
        return self.create_alert(
            alert_type=AlertType.CONCENTRATION_BREACH,
            severity=AlertSeverity.WARNING,
            message=f"Collateral concentration limit breached: {', '.join(breaches)}",
            account_id=account_id,
            data={'breaches': breaches}
        )
    
    def alert_payment_received(
        self,
        account_id: str,
        call_id: str,
        amount: float,
        remaining: float
    ) -> Alert:
        """
        Create payment received alert.
        
        Parameters:
            account_id: Account identifier
            call_id: Margin call ID
            amount: Amount received
            remaining: Remaining amount
        
        Returns:
            Created alert
        """
        if remaining <= 0:
            return self.create_alert(
                alert_type=AlertType.CALL_SATISFIED,
                severity=AlertSeverity.INFO,
                message=f"Margin call {call_id} fully satisfied with payment of ${amount:,.2f}",
                account_id=account_id,
                data={'call_id': call_id, 'amount': amount}
            )
        else:
            return self.create_alert(
                alert_type=AlertType.PAYMENT_RECEIVED,
                severity=AlertSeverity.INFO,
                message=f"Payment of ${amount:,.2f} received for call {call_id}. "
                        f"Remaining: ${remaining:,.2f}",
                account_id=account_id,
                data={'call_id': call_id, 'amount': amount, 'remaining': remaining}
            )
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert.
        
        Parameters:
            alert_id: Alert identifier
            acknowledged_by: User acknowledging
        
        Returns:
            True if acknowledged successfully
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.is_acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        return True
    
    def get_unacknowledged_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get all unacknowledged alerts.
        
        Parameters:
            severity: Filter by severity (optional)
        
        Returns:
            List of unacknowledged alerts
        """
        alerts = [a for a in self.alerts.values() if not a.is_acknowledged]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alerts_by_account(self, account_id: str) -> List[Alert]:
        """Get all alerts for an account."""
        return [a for a in self.alerts.values() if a.account_id == account_id]
    
    def get_alert_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get alert history as DataFrame.
        
        Parameters:
            start_date: Filter start date (optional)
            end_date: Filter end date (optional)
        
        Returns:
            DataFrame with alert history
        """
        rows = [a.to_dict() for a in self.alerts.values()]
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if start_date:
            df = df[df['timestamp'] >= start_date]
        if end_date:
            df = df[df['timestamp'] <= end_date]
        
        return df.sort_values('timestamp', ascending=False)
    
    def get_alert_summary(self) -> Dict:
        """
        Get summary of alerts.
        
        Returns:
            Dictionary with alert summary
        """
        total = len(self.alerts)
        unacked = sum(1 for a in self.alerts.values() if not a.is_acknowledged)
        
        by_severity = {}
        for sev in AlertSeverity:
            by_severity[sev.value] = sum(
                1 for a in self.alerts.values() if a.severity == sev
            )
        
        by_type = {}
        for atype in AlertType:
            by_type[atype.value] = sum(
                1 for a in self.alerts.values() if a.alert_type == atype
            )
        
        return {
            'total_alerts': total,
            'unacknowledged': unacked,
            'by_severity': by_severity,
            'by_type': by_type
        }


if __name__ == "__main__":
    print("Testing Alert System...")
    
    # Create alert system
    alert_system = AlertSystem(
        warning_threshold=80,
        critical_threshold=95,
        emergency_threshold=110
    )
    
    # Test margin utilization alerts
    print("\nTesting utilization alerts:")
    alert_system.check_margin_utilization("ACCT-001", 75.0)  # No alert
    alert_system.check_margin_utilization("ACCT-001", 85.0)  # Warning
    alert_system.check_margin_utilization("ACCT-002", 98.0)  # Critical
    alert_system.check_margin_utilization("ACCT-003", 115.0) # Emergency
    
    # Test margin call alert
    print("\nTesting margin call alert:")
    alert_system.alert_margin_call(
        account_id="ACCT-001",
        call_id="MC-001",
        amount=50000,
        due_date=datetime.now()
    )
    
    # Test payment received
    print("\nTesting payment alert:")
    alert_system.alert_payment_received(
        account_id="ACCT-001",
        call_id="MC-001",
        amount=30000,
        remaining=20000
    )
    
    # Get summary
    summary = alert_system.get_alert_summary()
    print(f"\nAlert Summary:")
    print(f"  Total: {summary['total_alerts']}")
    print(f"  Unacknowledged: {summary['unacknowledged']}")
    print(f"  By Severity: {summary['by_severity']}")
