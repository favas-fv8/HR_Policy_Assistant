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
      <div style={{ maxWidth: '600px', margin: '5rem auto', padding: '2rem', background: '#fff', borderRadius: '8px', textAlign: 'center' }}>
        <h2 style={{ color: '#dc3545', marginBottom: '1rem' }}>Access Denied</h2>
        <p style={{ color: '#555' }}>Only HR Admins can manage employee accounts.</p>
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

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.6rem',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '0.95rem',
    marginBottom: '0.5rem',
  };

  const labelStyle: React.CSSProperties = { display: 'block', marginBottom: '0.25rem', color: '#333', fontSize: '0.9rem', textAlign: 'left' };

  const buttonStyle: React.CSSProperties = {
    padding: '0.5rem 1rem',
    background: '#2c3e50',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '0.9rem',
    cursor: 'pointer',
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1a1a2e', marginBottom: '0.5rem' }}>Employee Management</h1>
      <p style={{ color: '#52525b', marginBottom: '2rem' }}>Create and manage employee accounts.</p>

      {error && <p style={{ color: '#e74c32', marginBottom: '1rem' }}>{error}</p>}
      {success && <p style={{ color: '#27ae60', marginBottom: '1rem' }}>{success}</p>}

      <section style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '1rem' }}>Create Employee</h2>
        <form onSubmit={handleCreate} style={{ maxWidth: '700px' }}>
          <div style={{ marginBottom: '0.5rem' }}>
            <label style={labelStyle}>Employee ID (will be used as User ID)</label>
            <input
              style={inputStyle}
              value={form.employeeId}
              onChange={(e) => setForm({ ...form, employeeId: e.target.value })}
              required
            />
            {fieldErrors.employeeId && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{fieldErrors.employeeId}</div>}
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <label style={labelStyle}>Full Name</label>
            <input
              style={inputStyle}
              value={form.fullName}
              onChange={(e) => setForm({ ...form, fullName: e.target.value })}
              required
            />
            {fieldErrors.fullName && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{fieldErrors.fullName}</div>}
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <label style={labelStyle}>Email</label>
            <input
              style={inputStyle}
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            {fieldErrors.email && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{fieldErrors.email}</div>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
            <div>
              <label style={labelStyle}>Password</label>
              <input
                style={inputStyle}
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
              {fieldErrors.password && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{fieldErrors.password}</div>}
            </div>
            <div>
              <label style={labelStyle}>Confirm Password</label>
              <input
                style={inputStyle}
                type="password"
                value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                required
              />
              {fieldErrors.confirmPassword && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{fieldErrors.confirmPassword}</div>}
            </div>
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            style={{ ...buttonStyle, background: '#27ae60', marginTop: '0.5rem', opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
          >
            {isSubmitting ? 'Creating...' : 'Create Employee'}
          </button>
        </form>
      </section>

      <section style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
        <h2 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '1rem' }}>Employees</h2>
        {loading ? (
          <p>Loading employees...</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>Employee ID</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>User ID</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>Name</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>Email</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #eee' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{u.employee_id}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{u.username}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{u.full_name || u.username}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{u.email}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{u.is_active ? 'Active' : 'Inactive'}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    {u.role === 'hr_admin' ? (
                      <span style={{ color: '#666' }}>HR Admin</span>
                    ) : (
                      <>
                        <button type="button" style={buttonStyle} onClick={() => startEdit(u)}>Edit</button>{' '}
                        <button type="button" style={buttonStyle} onClick={() => toggleStatus(u)}>
                          {u.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        {' '}
                        <button type="button" style={{ ...buttonStyle, background: '#c0392b' }} onClick={() => handleDelete(u)}>
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
        <section style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', marginTop: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '1rem' }}>Edit Employee</h2>
          <form onSubmit={saveEdit} style={{ maxWidth: '500px' }}>
            <label style={labelStyle}>Employee ID (User ID)</label>
            <input style={inputStyle} value={editEmployeeId} onChange={(e) => setEditEmployeeId(e.target.value)} required />
            {editErrors.employeeId && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{editErrors.employeeId}</div>}
            <label style={labelStyle}>Full Name</label>
            <input style={inputStyle} value={editFullName} onChange={(e) => setEditFullName(e.target.value)} required />
            {editErrors.fullName && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{editErrors.fullName}</div>}
            <label style={labelStyle}>Email</label>
            <input style={inputStyle} type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} required />
            {editErrors.email && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{editErrors.email}</div>}
            {editErrors.general && <div style={{ color: '#e74c32', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{editErrors.general}</div>}
            <button type="submit" disabled={isEditing} style={{ ...buttonStyle, background: '#f39c12', marginTop: '0.5rem', opacity: isEditing ? 0.7 : 1 }}>
              {isEditing ? 'Saving...' : 'Save Changes'}
            </button>{' '}
            <button type="button" style={buttonStyle} onClick={() => setEditUser(null)}>Cancel</button>
          </form>
        </section>
      )}

      <button type="button" onClick={loadUsers} style={{ ...buttonStyle, background: '#3498db', marginTop: '1rem' }}>Refresh</button>
    </div>
  );
}
