import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) =>
    apiClient.post('/auth/login', { email, password }),
  
  getCurrentVendor: () =>
    apiClient.get('/auth/me'),
  
  logout: () =>
    apiClient.post('/auth/logout'),
};

// Projects API
export const projectsAPI = {
  getAvailableProjects: () =>
    apiClient.get('/vendors/projects'),
};

// Applications API
export const applicationsAPI = {
  getAll: () =>
    apiClient.get('/applications'),
  
  getById: (id) =>
    apiClient.get(`/applications/${id}`),
  
  create: (projectId) =>
    apiClient.post('/applications', { project_id: projectId }),
  
  delete: (id) =>
    apiClient.delete(`/applications/${id}`),
};

// Form 1 API
export const form1API = {
  getData: (applicationId) =>
    apiClient.get(`/forms/1/${applicationId}`),
  
  createProject: (applicationId, projectData) =>
    apiClient.post(`/forms/1/${applicationId}/projects`, projectData),
  
  updateProject: (projectId, projectData) =>
    apiClient.put(`/forms/1/projects/${projectId}`, projectData),
  
  deleteProject: (projectId) =>
    apiClient.delete(`/forms/1/projects/${projectId}`),
  
  submit: (applicationId) =>
    apiClient.post(`/forms/1/${applicationId}/submit`),
};


export const form2API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/2/${applicationId}`),
    
    createProject: (applicationId, data) => 
      apiClient.post(`/forms/2/${applicationId}/projects`, data),
    
    updateProject: (projectId, data) => 
      apiClient.put(`/forms/2/projects/${projectId}`, data),
    
    deleteProject: (projectId) => 
      apiClient.delete(`/forms/2/projects/${projectId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/2/${applicationId}/submit`),
  };


  // Form 3 API
export const form3API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/3/${applicationId}`),
    
    createProfile: (applicationId, data) => 
      apiClient.post(`/forms/3/${applicationId}/profiles`, data),
    
    updateProfile: (profileId, data) => 
      apiClient.put(`/forms/3/profiles/${profileId}`, data),
    
    deleteProfile: (profileId) => 
      apiClient.delete(`/forms/3/profiles/${profileId}`),
    
    // Personnel
    addPersonnel: (profileId, data) => 
      apiClient.post(`/forms/3/profiles/${profileId}/personnel`, data),
    
    deletePersonnel: (personnelId) => 
      apiClient.delete(`/forms/3/personnel/${personnelId}`),
    
    // Equipment
    addEquipment: (profileId, data) => 
      apiClient.post(`/forms/3/profiles/${profileId}/equipment`, data),
    
    deleteEquipment: (equipmentId) => 
      apiClient.delete(`/forms/3/equipment/${equipmentId}`),
    
    // Materials
    addMaterial: (profileId, data) => 
      apiClient.post(`/forms/3/profiles/${profileId}/materials`, data),
    
    deleteMaterial: (materialId) => 
      apiClient.delete(`/forms/3/materials/${materialId}`),
    
    // Subcontractors
    addSubcontractor: (profileId, data) => 
      apiClient.post(`/forms/3/profiles/${profileId}/subcontractors`, data),
    
    deleteSubcontractor: (subcontractorId) => 
      apiClient.delete(`/forms/3/subcontractors/${subcontractorId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/3/${applicationId}/submit`),
  };


// Form 4 API
export const form4API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/4/${applicationId}`),
    
    createPersonnel: (applicationId, data) => 
      apiClient.post(`/forms/4/${applicationId}/personnel`, data),
    
    updatePersonnel: (personnelId, data) => 
      apiClient.put(`/forms/4/personnel/${personnelId}`, data),
    
    deletePersonnel: (personnelId) => 
      apiClient.delete(`/forms/4/personnel/${personnelId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/4/${applicationId}/submit`),
  };


// Form 5 API
export const form5API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/5/${applicationId}`),
    
    createResume: (applicationId, data) => 
      apiClient.post(`/forms/5/${applicationId}/resumes`, data),
    
    updateResume: (resumeId, data) => 
      apiClient.put(`/forms/5/resumes/${resumeId}`, data),
    
    deleteResume: (resumeId) => 
      apiClient.delete(`/forms/5/resumes/${resumeId}`),
    
    // Education
    addEducation: (resumeId, data) => 
      apiClient.post(`/forms/5/resumes/${resumeId}/education`, data),
    
    deleteEducation: (educationId) => 
      apiClient.delete(`/forms/5/education/${educationId}`),
    
    // Work Experience
    addWorkExperience: (resumeId, data) => 
      apiClient.post(`/forms/5/resumes/${resumeId}/work-experience`, data),
    
    deleteWorkExperience: (experienceId) => 
      apiClient.delete(`/forms/5/work-experience/${experienceId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/5/${applicationId}/submit`),
  };

// Form 6 API
export const form6API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/6/${applicationId}`),
    
    createManpower: (applicationId, data) => 
      apiClient.post(`/forms/6/${applicationId}/manpower`, data),
    
    updateManpower: (manpowerId, data) => 
      apiClient.put(`/forms/6/manpower/${manpowerId}`, data),
    
    deleteManpower: (manpowerId) => 
      apiClient.delete(`/forms/6/manpower/${manpowerId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/6/${applicationId}/submit`),
  };

  // Form 7 API
export const form7API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/7/${applicationId}`),
    
    createEquipment: (applicationId, data) => 
      apiClient.post(`/forms/7/${applicationId}/equipment`, data),
    
    updateEquipment: (equipmentId, data) => 
      apiClient.put(`/forms/7/equipment/${equipmentId}`, data),
    
    deleteEquipment: (equipmentId) => 
      apiClient.delete(`/forms/7/equipment/${equipmentId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/7/${applicationId}/submit`),
  };

// Form 8 API
export const form8API = {
    getData: (applicationId) => 
      apiClient.get(`/forms/8/${applicationId}`),
    
    createResponse: (applicationId, data) => 
      apiClient.post(`/forms/8/${applicationId}/responses`, data),
    
    uploadAttachment: (responseId, file) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post(`/forms/8/responses/${responseId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    },
    
    deleteAttachment: (attachmentId) => 
      apiClient.delete(`/forms/8/attachments/${attachmentId}`),
    
    submit: (applicationId) => 
      apiClient.post(`/forms/8/${applicationId}/submit`),
  };
// Documents API
export const documentsAPI = {
  upload: (formData) =>
    apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  getById: (documentId) =>
    apiClient.get(`/documents/${documentId}`),
  
  getFormDocuments: (applicationId, formNumber, relatedEntityId = null) => {
    const params = relatedEntityId ? { related_entity_id: relatedEntityId } : {};
    return apiClient.get(`/documents/form/${applicationId}/${formNumber}`, { params });
  },
  
  delete: (documentId) =>
    apiClient.delete(`/documents/${documentId}`),
  
  getDownloadUrl: (documentId) =>
    apiClient.get(`/documents/${documentId}/download-url`),
};

export default apiClient;