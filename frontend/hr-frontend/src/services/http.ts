export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export const getErrorMessage = (data: any, fallback: string, status: number): string => {
  if (data) {
    if (typeof data.detail === 'string') return data.detail;
    if (typeof data.error === 'string') return data.error;
    if (Array.isArray(data.non_field_errors) && data.non_field_errors.length) return data.non_field_errors[0];
    if (Array.isArray(data.title) && data.title.length) return data.title[0];
    if (Array.isArray(data.file) && data.file.length) return data.file[0];
    if (Array.isArray(data.old_password) && data.old_password.length) return data.old_password[0];
    if (Array.isArray(data.new_password1) && data.new_password1.length) return data.new_password1[0];
    if (Array.isArray(data.new_password2) && data.new_password2.length) return data.new_password2[0];
    if (Array.isArray(data.username) && data.username.length) return data.username[0];
    if (Array.isArray(data.email) && data.email.length) return data.email[0];
    if (Array.isArray(data.password) && data.password.length) return data.password[0];
    if (Array.isArray(data.employee_id) && data.employee_id.length) return data.employee_id[0];
    if (Array.isArray(data.confirm_password) && data.confirm_password.length) return data.confirm_password[0];
    if (Array.isArray(data.full_name) && data.full_name.length) return data.full_name[0];
  }
  if (status === 401) return 'Your session has expired. Please log in again.';
  if (status === 403) return 'You do not have permission to perform this action.';
  if (status === 404) return 'The requested resource was not found.';
  if (status >= 500) return 'A server error occurred. Please try again later.';
  return fallback;
};

export const apiFetch = async <T = any>(url: string, options: RequestInit = {}): Promise<T> => {
  const resp = await fetch(url, options);
  const text = await resp.text();
  let data: any = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!resp.ok) {
    throw new ApiError(getErrorMessage(data, 'Request failed.', resp.status), resp.status, data);
  }
  return (data ?? {}) as T;
};
