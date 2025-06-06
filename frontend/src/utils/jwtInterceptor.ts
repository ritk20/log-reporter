type RequestOptions = RequestInit & {
  headers: HeadersInit;
};

export async function fetchWithAuth(url: string, options: RequestOptions = { headers: {} }): Promise<Response> {
  // Get the token from localStorage
  const token = localStorage.getItem('authToken');
  
  // Merge default and custom headers
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(`http://localhost:8000${url}`, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized responses
    if (response.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
      throw new Error('Session expired');
    }

    // Handle other non-200 responses
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;

  } catch (error) {
    // Handle network errors or other exceptions
    console.error('Fetch error:', error);
    throw error;
  }
}

// Helper methods for common HTTP methods
export const api = {
  async get<T>(url: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, { 
      ...(options || {}), 
      method: 'GET',
      headers: options?.headers ?? {},
    });
    return response.json();
  },

  async post<T, D = unknown>(url: string, data?: D, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...(options || {}),
      method: 'POST',
      body: JSON.stringify(data),
      headers: options?.headers ?? {},
    });
    return response.json();
  },

  async put<T, D = unknown>(url: string, data?: D, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...(options || {}),
      method: 'PUT',
      body: JSON.stringify(data),
      headers: options?.headers ?? {},
    });
    return response.json();
  },

  async delete<T>(url: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...(options || {}),
      method: 'DELETE',
      headers: options?.headers ?? {},
    });
    return response.json();
  }
};