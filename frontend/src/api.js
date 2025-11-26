import axios from 'axios';

// Configuration Axios avec JWT
const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Intercepteur pour ajouter le token JWT
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Intercepteur pour gérer les erreurs
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('accessToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentification
  async login(email, password) {
    const response = await this.client.post('/foundation/auth/login/', {
      email,
      password,
    });
    
    const { access, refresh } = response.data.tokens;
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
    
    return response.data;
  }

  async logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  // Schéma de projet
  async getProjectSchema(projectId) {
    const response = await this.client.get(`/runtime/projects/${projectId}/schema/`);
    return response.data;
  }

  async getTableSchema(projectId, tableName) {
    const response = await this.client.get(`/runtime/projects/${projectId}/tables/${tableName}/schema/`);
    return response.data;
  }

  // CRUD Operations
  async getTableData(projectId, tableName, params = {}) {
    const response = await this.client.get(`/runtime/projects/${projectId}/tables/${tableName}/`, {
      params,
    });
    return response.data;
  }

  async createRecord(projectId, tableName, data) {
    const response = await this.client.post(`/runtime/projects/${projectId}/tables/${tableName}/`, data);
    return response.data;
  }

  async updateRecord(projectId, tableName, id, data) {
    const response = await this.client.put(`/runtime/projects/${projectId}/tables/${tableName}/${id}/`, data);
    return response.data;
  }

  async deleteRecord(projectId, tableName, id) {
    await this.client.delete(`/runtime/projects/${projectId}/tables/${tableName}/${id}/`);
  }
}

export default new ApiService();
