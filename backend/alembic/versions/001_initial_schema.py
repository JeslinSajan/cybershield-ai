"""Initial schema - all 25 tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-01 20:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('slug', sa.String(80), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])

    # Create roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )

    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource', sa.String(80), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('resource', 'action')
    )

    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('role_id', 'permission_id')
    )
    op.create_index('idx_role_permissions_role_id', 'role_permissions', ['role_id'])
    op.create_foreign_key('fk_role_permissions_role_id', 'role_permissions', 'roles', ['role_id'], ['id'])
    op.create_foreign_key('fk_role_permissions_permission_id', 'role_permissions', 'permissions', ['permission_id'], ['id'])

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(80), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_users_org_email', 'users', ['organization_id', 'email'])
    op.create_index('idx_users_role_id', 'users', ['role_id'])
    op.create_index('idx_users_org_active', 'users', ['organization_id', 'is_active'])
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])

    # Create agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('hostname', sa.String(120), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_agents_org_status', 'agents', ['organization_id', 'status'])
    op.create_index('idx_agents_last_heartbeat', 'agents', ['last_heartbeat_at'])
    op.create_index('idx_agents_active', 'agents', ['is_active'])
    op.create_foreign_key('fk_agents_organization_id', 'agents', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create agent_credentials table
    op.create_table('agent_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential_hash', sa.String(255), nullable=False),
        sa.Column('type', sa.String(30), nullable=False, server_default='token'),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_agent_credentials_agent_active', 'agent_credentials', ['agent_id', 'is_active'])
    op.create_index('idx_agent_credentials_expires_at', 'agent_credentials', ['expires_at'])
    op.create_foreign_key('fk_agent_credentials_agent_id', 'agent_credentials', 'agents', ['agent_id'], ['id'])

    # Create agent_heartbeats table
    op.create_table('agent_heartbeats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('cpu_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('memory_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_agent_heartbeats_agent_time', 'agent_heartbeats', ['agent_id', 'timestamp'])
    op.create_index('idx_agent_heartbeats_org_time', 'agent_heartbeats', ['organization_id', 'timestamp'])
    op.create_foreign_key('fk_agent_heartbeats_agent_id', 'agent_heartbeats', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_agent_heartbeats_organization_id', 'agent_heartbeats', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create devices table
    op.create_table('devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=False),
        sa.Column('mac_address', sa.String(17), nullable=True),
        sa.Column('hostname', sa.String(120), nullable=True),
        sa.Column('vendor', sa.String(120), nullable=True),
        sa.Column('device_type', sa.String(40), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='unknown'),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('organization_id', 'ip_address')
    )
    op.create_index('idx_devices_org_status', 'devices', ['organization_id', 'status'])
    op.create_index('idx_devices_agent_id', 'devices', ['agent_id'])
    op.create_index('idx_devices_last_seen', 'devices', ['last_seen_at'])
    op.create_foreign_key('fk_devices_organization_id', 'devices', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_devices_agent_id', 'devices', 'agents', ['agent_id'], ['id'])

    # Create device_interfaces table
    op.create_table('device_interfaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(80), nullable=False),
        sa.Column('mac_address', sa.String(17), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('bytes_sent', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('bytes_received', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_device_interfaces_device_id', 'device_interfaces', ['device_id'])
    op.create_index('idx_device_interfaces_org_device', 'device_interfaces', ['organization_id', 'device_id'])
    op.create_foreign_key('fk_device_interfaces_organization_id', 'device_interfaces', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_device_interfaces_device_id', 'device_interfaces', 'devices', ['device_id'], ['id'])

    # Create scans table
    op.create_table('scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_type', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('target_scope', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_scans_org_status', 'scans', ['organization_id', 'status'])
    op.create_index('idx_scans_agent_id', 'scans', ['agent_id'])
    op.create_index('idx_scans_created_by_user', 'scans', ['created_by_user_id'])
    op.create_foreign_key('fk_scans_organization_id', 'scans', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_scans_agent_id', 'scans', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_scans_created_by_user_id', 'scans', 'users', ['created_by_user_id'], ['id'])

    # Create scan_results table
    op.create_table('scan_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('result_type', sa.String(30), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_scan_results_scan_id', 'scan_results', ['scan_id'])
    op.create_index('idx_scan_results_device_id', 'scan_results', ['device_id'])
    op.create_index('idx_scan_results_org_scan', 'scan_results', ['organization_id', 'scan_id'])
    op.create_foreign_key('fk_scan_results_organization_id', 'scan_results', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_scan_results_scan_id', 'scan_results', 'scans', ['scan_id'], ['id'])
    op.create_foreign_key('fk_scan_results_device_id', 'scan_results', 'devices', ['device_id'], ['id'])

    # Create cves table
    op.create_table('cves',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cve_id', sa.String(50), nullable=False, unique=True),
        sa.Column('severity', sa.String(15), nullable=False),
        sa.Column('cvss_score', sa.Numeric(4, 1), nullable=True),
        sa.Column('affected_service', sa.String(80), nullable=True),
        sa.Column('affected_version', sa.String(120), nullable=True),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('source', sa.String(40), nullable=False, server_default='local_seed'),
        sa.Column('is_demo_data', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_cves_org_severity', 'cves', ['organization_id', 'severity'])
    op.create_index('idx_cves_service_version', 'cves', ['affected_service', 'affected_version'])
    op.create_index('idx_cves_cve_id', 'cves', ['cve_id'])
    op.create_foreign_key('fk_cves_organization_id', 'cves', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create vulnerabilities table
    op.create_table('vulnerabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cve_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('severity', sa.String(15), nullable=False),
        sa.Column('score', sa.Numeric(5, 2), nullable=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('status', sa.String(25), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_vulnerabilities_org_device', 'vulnerabilities', ['organization_id', 'device_id'])
    op.create_index('idx_vulnerabilities_severity', 'vulnerabilities', ['severity'])
    op.create_index('idx_vulnerabilities_scan_id', 'vulnerabilities', ['scan_id'])
    op.create_foreign_key('fk_vulnerabilities_organization_id', 'vulnerabilities', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_vulnerabilities_device_id', 'vulnerabilities', 'devices', ['device_id'], ['id'])
    op.create_foreign_key('fk_vulnerabilities_scan_id', 'vulnerabilities', 'scans', ['scan_id'], ['id'])
    op.create_foreign_key('fk_vulnerabilities_cve_id', 'vulnerabilities', 'cves', ['cve_id'], ['id'])

    # Create logs table
    op.create_table('logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('username', sa.String(120), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_logs_org_time', 'logs', ['organization_id', 'timestamp'])
    op.create_index('idx_logs_agent_id', 'logs', ['agent_id'])
    op.create_index('idx_logs_device_id', 'logs', ['device_id'])
    op.create_index('idx_logs_severity', 'logs', ['severity'])
    op.create_foreign_key('fk_logs_organization_id', 'logs', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_logs_agent_id', 'logs', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_logs_device_id', 'logs', 'devices', ['device_id'], ['id'])

    # Create threat_indicators table
    op.create_table('threat_indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_type', sa.String(20), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='local'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'indicator_type', 'value')
    )
    op.create_index('idx_threat_indicators_type_value', 'threat_indicators', ['indicator_type', 'value'])
    op.create_foreign_key('fk_threat_indicators_organization_id', 'threat_indicators', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(40), nullable=False),
        sa.Column('severity', sa.String(15), nullable=False),
        sa.Column('status', sa.String(25), nullable=False, server_default='Open'),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_alerts_org_status', 'alerts', ['organization_id', 'status'])
    op.create_index('idx_alerts_severity', 'alerts', ['severity'])
    op.create_index('idx_alerts_device_id', 'alerts', ['device_id'])
    op.create_index('idx_alerts_triggered_at', 'alerts', ['triggered_at'])
    op.create_foreign_key('fk_alerts_organization_id', 'alerts', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_alerts_agent_id', 'alerts', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_alerts_device_id', 'alerts', 'devices', ['device_id'], ['id'])

    # Create alert_events table
    op.create_table('alert_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_status', sa.String(25), nullable=True),
        sa.Column('to_status', sa.String(25), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_alert_events_alert_changed_at', 'alert_events', ['alert_id', 'changed_at'])
    op.create_foreign_key('fk_alert_events_organization_id', 'alert_events', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_alert_events_alert_id', 'alert_events', 'alerts', ['alert_id'], ['id'])
    op.create_foreign_key('fk_alert_events_actor_user_id', 'alert_events', 'users', ['actor_user_id'], ['id'])

    # Create risk_scores table
    op.create_table('risk_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(30), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Numeric(5, 2), nullable=False),
        sa.Column('risk_band', sa.String(20), nullable=False),
        sa.Column('factor_breakdown', sa.String(), nullable=False),
        sa.Column('formula_version', sa.String(40), nullable=False, server_default='v1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_risk_scores_org_entity', 'risk_scores', ['organization_id', 'entity_type', 'entity_id'])
    op.create_index('idx_risk_scores_band', 'risk_scores', ['risk_band'])
    op.create_foreign_key('fk_risk_scores_organization_id', 'risk_scores', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create reports table
    op.create_table('reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.String(30), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('mime_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='READY'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_reports_org_time', 'reports', ['organization_id', 'period_start'])
    op.create_index('idx_reports_created_by_user', 'reports', ['created_by_user_id'])
    op.create_foreign_key('fk_reports_organization_id', 'reports', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_reports_created_by_user_id', 'reports', 'users', ['created_by_user_id'], ['id'])

    # Create ai_conversations table
    op.create_table('ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_type', sa.String(30), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_type', sa.String(30), nullable=False, server_default='local_rule_ai'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_ai_conversations_user_id', 'ai_conversations', ['user_id'])
    op.create_index('idx_ai_conversations_org_subject', 'ai_conversations', ['organization_id', 'subject_type', 'subject_id'])
    op.create_foreign_key('fk_ai_conversations_organization_id', 'ai_conversations', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_ai_conversations_user_id', 'ai_conversations', 'users', ['user_id'], ['id'])

    # Create ai_messages table
    op.create_table('ai_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])
    op.create_foreign_key('fk_ai_messages_conversation_id', 'ai_messages', 'ai_conversations', ['conversation_id'], ['id'])

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.String(30), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False, server_default='dashboard'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_notifications_user_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_org_alert', 'notifications', ['organization_id', 'alert_id'])
    op.create_foreign_key('fk_notifications_organization_id', 'notifications', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_notifications_user_id', 'notifications', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_notifications_alert_id', 'notifications', 'alerts', ['alert_id'], ['id'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_type', sa.String(20), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(80), nullable=False),
        sa.Column('target_type', sa.String(80), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    op.create_index('idx_audit_logs_org_time', 'audit_logs', ['organization_id', 'created_at'])
    op.create_index('idx_audit_logs_actor_id', 'audit_logs', ['actor_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_foreign_key('fk_audit_logs_organization_id', 'audit_logs', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(120), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'key')
    )
    op.create_index('idx_system_settings_org_key', 'system_settings', ['organization_id', 'key'])
    op.create_foreign_key('fk_system_settings_organization_id', 'system_settings', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_system_settings_created_by_user_id', 'system_settings', 'users', ['created_by_user_id'], ['id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (to handle foreign key dependencies)
    op.drop_table('system_settings')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('ai_messages')
    op.drop_table('ai_conversations')
    op.drop_table('reports')
    op.drop_table('risk_scores')
    op.drop_table('alert_events')
    op.drop_table('alerts')
    op.drop_table('threat_indicators')
    op.drop_table('logs')
    op.drop_table('vulnerabilities')
    op.drop_table('cves')
    op.drop_table('scan_results')
    op.drop_table('scans')
    op.drop_table('device_interfaces')
    op.drop_table('devices')
    op.drop_table('agent_heartbeats')
    op.drop_table('agent_credentials')
    op.drop_table('agents')
    op.drop_table('users')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('organizations')
