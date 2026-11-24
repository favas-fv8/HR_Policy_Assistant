import type { User } from '../state/authContext';
import { apiFetch } from './http';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem('hr_token') ?? ''}` });

export const fetchCurrentUser = async (): Promise<User> => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/me/`, {
    headers: authHeaders(),
  });
  return data;
};

export const createUser = async (userData: {
  employee_id: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email: string;
  password: string;
  confirm_password: string;
}) => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(userData),
  });
  return data;
};

export const fetchUsers = async (): Promise<User[]> => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/`, {
    headers: authHeaders(),
  });
  return Array.isArray(data) ? data : [];
};

export const updateUser = async (
  userId: number,
  userData: {
    employee_id?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    full_name?: string;
  },
) => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/${userId}/update/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(userData),
  });
  return data;
};

export const deactivateUser = async (userId: number) => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/${userId}/deactivate/`, {
    method: 'POST',
    headers: authHeaders(),
  });
  return data;
};

export const reactivateUser = async (userId: number) => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/${userId}/reactivate/`, {
    method: 'POST',
    headers: authHeaders(),
  });
  return data;
};

export const deleteUser = async (userId: number) => {
  const data = await apiFetch(`${API_BASE}/v1/accounts/users/${userId}/delete/`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  return data;
};
