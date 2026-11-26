import { useEffect, useState } from 'react';
import { useAuth } from '../state/authContext';
import { fetchUsers, createUser, updateUser, deactivateUser, reactivateUser, deleteUser } from '../services/authService';
import type { User } from '../state/authContext';

interface EmployeeForm {
  employeeId: string;
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const emptyEmployeeForm: EmployeeForm = {
  employeeId: '',
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
};

type FieldErrors = Partial<Record<keyof EmployeeForm | 'general', string>>;

export default function EmployeesPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [success, setSuccess] = useState<string | null>(null);
  const [form, setForm] = useState<EmployeeForm>(emptyEmployeeForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editEmployeeId, setEditEmployeeId] = useState('');
  const [editFullName, setEditFullName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editErrors, setEditErrors] = useState<{ employeeId?: string; fullName?: string; email?: string; general?: string }>({});
  const [isEditing, setIsEditing] = useState(false);

  if (!user) {
    return null;
  }

  if (user.role !== 'hr_admin') {
    return (
      <div className="neural-page neural-page--narrow">
        <div className="neural-card neural-page__panel neural-page__panel--center">
          <h2 className="neural-page__error-title">Access Denied</h2>
          <p className="neural-page__muted">Only HR Admins can manage employee accounts.</p>
        </div>
      </div>
    );
  }

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load employees.');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const getFieldError = (data: any, ...keys: string[]) => {
    for (const key of keys) {
      const val = data?.[key];
      if (Array.isArray(val) && val.length) return String(val[0]);
      if (typeof val === 'string') return val;
    }
    return undefined;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setFieldErrors({});
    setSuccess(null);

    const employeeId = form.employeeId.trim();
    const fullName = form.fullName.trim();
    const email = form.email.trim();
    const nextErrors: FieldErrors = {};
    if (!employeeId) nextErrors.employeeId = 'Employee ID is required.';
    if (!fullName) nextErrors.fullName = 'Full name is required.';
    if (!email) nextErrors.email = 'Email is required.';
    if (!form.password) nextErrors.password = 'Password is required.';
    if (!form.confirmPassword) nextErrors.confirmPassword = 'Confirm password is required.';
    if (form.password && form.confirmPassword && form.password !== form.confirmPassword) {
      nextErrors.confirmPassword = 'Passwords do not match.';
    }
    if (Object.keys(nextErrors).length) {
      setFieldErrors(nextErrors);
      return;
    }

    const nameParts = fullName.split(/\s+/).filter(Boolean);
    const first_name = nameParts[0] ?? '';
    const last_name = nameParts.slice(1).join(' ');

    setIsSubmitting(true);
    try {
      const created = await createUser({
        employee_id: employeeId,
        full_name: fullName,
        first_name,
        last_name,
        email,
        password: form.password,
        confirm_password: form.confirmPassword,
      });
      const generatedUserId = created?.username || employeeId;
      setSuccess(`Employee account created. User ID: ${generatedUserId}. Share this User ID with the employee; do not share the password.`);
      setForm(emptyEmployeeForm);
      setFieldErrors({});
      setShowCreateForm(false);
      await loadUsers();
    } catch (e: any) {
      const data = e?.data;
      const next: FieldErrors = {};
      const employeeErr = getFieldError(data, 'employee_id', 'username');
      const emailErr = getFieldError(data, 'email');
      const passwordErr = getFieldError(data, 'password');
      const confirmErr = getFieldError(data, 'confirm_password', 'non_field_errors');
      const nameErr = getFieldError(data, 'full_name', 'first_name', 'last_name');
      if (employeeErr) next.employeeId = employeeErr;
      if (emailErr) next.email = emailErr;
      if (passwordErr) next.password = passwordErr;
      if (confirmErr) next.confirmPassword = confirmErr;
      if (nameErr) next.fullName = nameErr;
      if (Object.keys(next).length) {
        setFieldErrors(next);
      } else {
        setError(e?.message || 'Failed to create employee.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const startEdit = (u: User) => {
    setEditUser(u);
    setEditEmployeeId(u.employee_id ?? '');
    setEditFullName(u.full_name ?? u.username);
    setEditEmail(u.email ?? '');
    setEditErrors({});
    setError(null);
    setSuccess(null);
  };

  const saveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser || isEditing) return;
    setEditErrors({});
    setError(null);
    setSuccess(null);

    const employeeId = editEmployeeId.trim();
    const fullName = editFullName.trim();
    const email = editEmail.trim();
    const next: typeof editErrors = {};
    if (!employeeId) next.employeeId = 'Employee ID is required.';
    if (!fullName) next.fullName = 'Full name is required.';
    if (!email) next.email = 'Email is required.';
    if (Object.keys(next).length) { setEditErrors(next); return; }

    const parts = fullName.split(/\s+/).filter(Boolean);
    setIsEditing(true);
    try {
      const updated = await updateUser(editUser.id, {
        employee_id: employeeId,
        email,
        full_name: fullName,
        first_name: parts[0] ?? '',
        last_name: parts.slice(1).join(' '),
      });
      setSuccess(`Employee updated. User ID: ${updated?.username || employeeId}`);
      setEditUser(null);
      await loadUsers();
    } catch (e: any) {
      const data = e?.data;
      const mapped: typeof editErrors = {};
      const employeeErr = getFieldError(data, 'employee_id', 'username');
      const emailErr = getFieldError(data, 'email');
      const nameErr = getFieldError(data, 'full_name', 'first_name', 'last_name');
      if (employeeErr) mapped.employeeId = employeeErr;
      if (emailErr) mapped.email = emailErr;
      if (nameErr) mapped.fullName = nameErr;
      if (Object.keys(mapped).length) setEditErrors(mapped);
      else setError(e?.message || 'Failed to update employee.');
    } finally {
      setIsEditing(false);
    }
  };

  const toggleStatus = async (u: User) => {
    if (u.role === 'hr_admin') return;
    const action = u.is_active ? 'deactivate' : 'reactivate';
    if (!window.confirm(`Are you sure you want to ${action} ${u.username}?`)) return;
    setError(null);
    setSuccess(null);
    try {
      if (u.is_active) {
        await deactivateUser(u.id);
        setSuccess(`Employee deactivated: ${u.username}`);
      } else {
        await reactivateUser(u.id);
        setSuccess(`Employee reactivated: ${u.username}`);
      }
      await loadUsers();
    } catch (e: any) {
      setError(e?.message || 'Failed to update employee status.');
    }
  };

  const handleDelete = async (u: User) => {
    if (u.role === 'hr_admin') return;
    const ok = window.confirm(
      `Permanently delete ${u.username}? This cannot be undone.\n\nIf the employee has chat/document history, deletion will be blocked and you should deactivate instead.`
    );
    if (!ok) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteUser(u.id);
      setSuccess(`Employee deleted: ${u.username}`);
      if (editUser?.id === u.id) setEditUser(null);
      await loadUsers();
    } catch (e: any) {
      const detail = e?.data?.detail ? ` ${e.data.detail}` : '';
      const related = Array.isArray(e?.data?.related_records) ? ` Related: ${e.data.related_records.join(', ')}.` : '';
      setError((e?.message || 'Failed to delete employee.') + related + detail);
    }
  };

  return (
    <div className="neural-page employees-page">
      <div className="neural-card neural-page__panel">
        <h1 className="neural-page__title">Employee Management</h1>
        <p className="neural-page__subtitle">Create and manage employee accounts.</p>
      </div>

      {error && <p className="neural-page__message neural-page__message--error">{error}</p>}
      {success && <p className="neural-page__message neural-page__message--success">{success}</p>}

      <div className="employees-page__toolbar">
        <button
          type="button"
          className="neural-btn neural-btn--secondary"
          onClick={() => {
            setShowCreateForm((v) => !v);
            setFieldErrors({});
            setError(null);
          }}
        >
          {showCreateForm ? 'Close' : '+ Add Employee'}
        </button>
      </div>

      {showCreateForm && (
      <section className="neural-card neural-page__panel">
        <h2 className="neural-page__section-title">Create Employee</h2>
        <form onSubmit={handleCreate} className="employees-page__form">
          <div className="employees-page__field">
            <label className="neural-label">Employee ID (will be used as User ID)</label>
            <input
              className="neural-input"
              value={form.employeeId}
              onChange={(e) => setForm({ ...form, employeeId: e.target.value })}
              required
            />
            {fieldErrors.employeeId && <div className="neural-field-error">{fieldErrors.employeeId}</div>}
          </div>
          <div className="employees-page__field">
            <label className="neural-label">Full Name</label>
            <input
              className="neural-input"
              value={form.fullName}
              onChange={(e) => setForm({ ...form, fullName: e.target.value })}
              required
            />
            {fieldErrors.fullName && <div className="neural-field-error">{fieldErrors.fullName}</div>}
          </div>
          <div className="employees-page__field">
            <label className="neural-label">Email</label>
            <input
              className="neural-input"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            {fieldErrors.email && <div className="neural-field-error">{fieldErrors.email}</div>}
          </div>
          <div className="employees-page__grid2">
            <div>
              <label className="neural-label">Password</label>
              <input
                className="neural-input"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
              {fieldErrors.password && <div className="neural-field-error">{fieldErrors.password}</div>}
            </div>
            <div>
              <label className="neural-label">Confirm Password</label>
              <input
                className="neural-input"
                type="password"
                value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                required
              />
              {fieldErrors.confirmPassword && <div className="neural-field-error">{fieldErrors.confirmPassword}</div>}
            </div>
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="neural-btn neural-btn--primary employees-page__submit" style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
          >
            {isSubmitting ? 'Creating...' : 'Create Employee'}
          </button>
        </form>
      </section>
      )}

      <section className="neural-card neural-page__panel">
        <h2 className="neural-page__section-title">Employees</h2>
        {loading ? (
          <p className="neural-page__muted">Loading employees...</p>
        ) : (
          <table className="neural-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>User ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.employee_id}</td>
                  <td>{u.username}</td>
                  <td>{u.full_name || u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    {u.role === 'hr_admin' ? (
                      <span className="neural-page__muted">HR Admin</span>
                    ) : (
                      <>
                        <button type="button" className="neural-btn neural-btn--secondary" onClick={() => startEdit(u)}>Edit</button>{' '}
                        <button type="button" className="neural-btn neural-btn--secondary" onClick={() => toggleStatus(u)}>
                          {u.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        {' '}
                        <button type="button" className="neural-btn neural-btn--danger" onClick={() => handleDelete(u)}>
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {editUser && (
        <section className="neural-card neural-page__panel">
          <h2 className="neural-page__section-title">Edit Employee</h2>
          <form onSubmit={saveEdit} className="employees-page__form employees-page__form--narrow">
            <label className="neural-label">Employee ID (User ID)</label>
            <input className="neural-input" value={editEmployeeId} onChange={(e) => setEditEmployeeId(e.target.value)} required />
            {editErrors.employeeId && <div className="neural-field-error">{editErrors.employeeId}</div>}
            <label className="neural-label">Full Name</label>
            <input className="neural-input" value={editFullName} onChange={(e) => setEditFullName(e.target.value)} required />
            {editErrors.fullName && <div className="neural-field-error">{editErrors.fullName}</div>}
            <label className="neural-label">Email</label>
            <input className="neural-input" type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} required />
            {editErrors.email && <div className="neural-field-error">{editErrors.email}</div>}
            {editErrors.general && <div className="neural-field-error">{editErrors.general}</div>}
            <button type="submit" disabled={isEditing} className="neural-btn neural-btn--primary employees-page__submit" style={{ opacity: isEditing ? 0.7 : 1 }}>
              {isEditing ? 'Saving...' : 'Save Changes'}
            </button>{' '}
            <button type="button" className="neural-btn neural-btn--secondary" onClick={() => setEditUser(null)}>Cancel</button>
          </form>
        </section>
      )}

      <button type="button" onClick={loadUsers} className="neural-btn neural-btn--primary employees-page__refresh">Refresh</button>
    </div>
  );
}




