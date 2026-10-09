import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { useAuth } from '../contexts/AuthContext';
import { usersService, UserItem, CreateUserData } from '../services/usersService';

export function Settings() {
  const { user, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'users' | 'system'>('profile');

  // User Management State (Admin only)
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState<boolean>(false);
  const [userError, setUserError] = useState<string | null>(null);

  // Create User Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [createEmail, setCreateEmail] = useState<string>('');
  const [createUsername, setCreateUsername] = useState<string>('');
  const [createPassword, setCreatePassword] = useState<string>('');
  const [createRoleId, setCreateRoleId] = useState<string>('');
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<boolean>(false);

  // Deactivate User Modal State
  const [userToDeactivate, setUserToDeactivate] = useState<UserItem | null>(null);
  const [isDeactivating, setIsDeactivating] = useState<boolean>(false);

  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return;
    setIsLoadingUsers(true);
    setUserError(null);
    try {
      const data = await usersService.listUsers();
      setUsers(data);
      // Auto-set default role_id if available
      if (data.length > 0 && !createRoleId) {
        setCreateRoleId(data[0].role_id);
      }
    } catch (err: any) {
      setUserError(err?.message || 'Failed to retrieve organization users.');
    } finally {
      setIsLoadingUsers(false);
    }
  }, [isAdmin, createRoleId]);

  useEffect(() => {
    if (activeTab === 'users' && isAdmin) {
      fetchUsers();
    }
  }, [activeTab, isAdmin, fetchUsers]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.organization_id || !createEmail.trim() || !createPassword) return;

    setIsCreatingUser(true);
    setCreateError(null);
    setCreateSuccess(false);

    try {
      const payload: CreateUserData = {
        organization_id: user.organization_id,
        role_id: createRoleId || user.role_id,
        email: createEmail.trim(),
        username: createUsername.trim() || undefined,
        password: createPassword,
      };

      await usersService.createUser(payload);
      setCreateSuccess(true);
      fetchUsers();
      setTimeout(() => {
        setIsCreateModalOpen(false);
        setCreateEmail('');
        setCreateUsername('');
        setCreatePassword('');
        setCreateSuccess(false);
      }, 1500);
    } catch (err: any) {
      setCreateError(err?.message || 'Failed to create user account.');
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleDeactivate = async () => {
    if (!userToDeactivate) return;
    setIsDeactivating(true);
    try {
      await usersService.deactivateUser(userToDeactivate.id);
      setUserToDeactivate(null);
      fetchUsers();
    } catch (err: any) {
      setUserError(err?.message || 'Failed to deactivate user.');
    } finally {
      setIsDeactivating(false);
    }
  };

  const userHeaders = ['Email', 'Username', 'Role ID', 'Account Status', 'Last Login', 'Actions'];
  const userRows = users.map((u) => [
    <span className="font-semibold text-white text-xs">{u.email}</span>,
    <span className="text-slate-300 text-xs">{u.username || <span className="text-slate-500 italic">None</span>}</span>,
    <span className="font-mono text-slate-400 text-[11px] truncate max-w-[120px] block" title={u.role_id}>
      {u.role_id}
    </span>,
    <Badge severity={u.is_active ? 'success' : 'danger'}>
      {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
    </Badge>,
    <span className="text-slate-400 text-xs font-mono">
      {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
    </span>,
    <div>
      {u.is_active && u.id !== user?.id && (
        <Button
          variant="danger"
          size="sm"
          onClick={() => setUserToDeactivate(u)}
        >
          Deactivate
        </Button>
      )}
      {u.id === user?.id && (
        <span className="text-[11px] text-cyan-400 font-mono">(Current User)</span>
      )}
    </div>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">System Settings & Administration</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage your personal profile, provision authorized users, and review platform configurations.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-2 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-3 px-3 border-b-2 transition-colors ${
            activeTab === 'profile'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          User Profile
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`pb-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'users'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>User Management</span>
          {isAdmin ? (
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              Admin
            </span>
          ) : (
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-500">
              Locked
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('system')}
          className={`pb-3 px-3 border-b-2 transition-colors ${
            activeTab === 'system'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Platform Settings
        </button>
      </div>

      {/* PROFILE TAB */}
      {activeTab === 'profile' && (
        <Card title="Current Identity Profile" description="Authenticated session parameters">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Email</span>
              <p className="text-slate-200 mt-1">{user?.email}</p>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Assigned Role</span>
              <div className="mt-1">
                <Badge severity="info">{user?.role || 'Viewer'}</Badge>
              </div>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">User UUID</span>
              <p className="text-slate-400 mt-1 truncate">{user?.id}</p>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Organization UUID</span>
              <p className="text-slate-400 mt-1 truncate">{user?.organization_id}</p>
            </div>
          </div>
        </Card>
      )}

      {/* USER MANAGEMENT TAB (ADMIN ONLY) */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {!isAdmin ? (
            <EmptyState
              title="Administrator Role Required"
              description="User account management, role assignment, and access revocation are restricted to platform Administrators (FR-2.1)."
            />
          ) : (
            <Card
              title="Authorized Organization Users"
              description="Users provisioned to access this CyberShield AI organization"
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setCreateEmail('');
                    setCreateUsername('');
                    setCreatePassword('');
                    setCreateError(null);
                    setCreateSuccess(false);
                    setIsCreateModalOpen(true);
                  }}
                  icon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                    </svg>
                  }
                >
                  + Provision New User
                </Button>
              }
            >
              {userError && (
                <div className="mb-4 p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
                  {userError}
                </div>
              )}

              {isLoadingUsers ? (
                <LoadingSpinner size="md" message="Loading users from backend..." />
              ) : users.length === 0 ? (
                <EmptyState
                  title="No users found"
                  description="No users found for this organization."
                />
              ) : (
                <Table headers={userHeaders} rows={userRows} />
              )}
            </Card>
          )}
        </div>
      )}

      {/* PLATFORM SETTINGS TAB */}
      {activeTab === 'system' && (
        <Card title="System Settings Configuration" description="Environment & security controls">
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">System Key-Value Store</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                  Phase 22 Feature
                </span>
              </div>
              <p className="text-slate-400">
                Arbitrary key-value configuration (<code className="text-cyan-300 font-mono">/api/v1/settings/</code>)
                is scheduled for Phase 22 security hardening. Current application settings are defined via backend environment variables.
              </p>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
              <span className="font-semibold text-slate-200">Active Security Configurations:</span>
              <ul className="text-slate-300 space-y-1 font-mono text-[11px]">
                <li>• Authentication Lockout: 5 failed attempts &rarr; 10-minute lock (FR-1.5)</li>
                <li>• Agent Offline Threshold: 90 seconds heartbeat silence</li>
                <li>• Threat Detection Rules: 3 active behavioral rules (Phase 15)</li>
                <li>• Password Cryptography: bcrypt hashing with individual salt</li>
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* CREATE USER MODAL */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Provision Authorized User Account"
        description="Creates a new credentialed user in your organization with role-based permissions."
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          {createError && (
            <div className="p-2.5 rounded bg-rose-950/70 border border-rose-800 text-xs text-rose-300">
              {createError}
            </div>
          )}

          {createSuccess && (
            <div className="p-2.5 rounded bg-emerald-950/70 border border-emerald-800 text-xs text-emerald-300">
              User account successfully created!
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
            <input
              type="email"
              value={createEmail}
              onChange={(e) => setCreateEmail(e.target.value)}
              placeholder="analyst@domain.com"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Username (Optional)</label>
            <input
              type="text"
              value={createUsername}
              onChange={(e) => setCreateUsername(e.target.value)}
              placeholder="e.g. jdoe"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Password</label>
            <input
              type="password"
              value={createPassword}
              onChange={(e) => setCreatePassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isCreatingUser}
            >
              Create User
            </Button>
          </div>
        </form>
      </Modal>

      {/* CONFIRM DEACTIVATE MODAL */}
      <Modal
        isOpen={!!userToDeactivate}
        onClose={() => setUserToDeactivate(null)}
        title="Deactivate User Account"
        description="Soft-deactivation of user access permissions."
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            Are you sure you want to deactivate <strong className="text-white">{userToDeactivate?.email}</strong>?
          </p>
          <p className="text-xs text-amber-400 bg-amber-950/40 p-2.5 rounded border border-amber-900/50">
            Deactivated accounts cannot authenticate or obtain API tokens. Note that under FR-2.3, the last remaining Administrator cannot be deactivated.
          </p>

          <div className="pt-3 flex justify-end gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setUserToDeactivate(null)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isDeactivating}
              onClick={handleDeactivate}
            >
              Confirm Deactivation
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
