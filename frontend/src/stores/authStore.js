import { create } from 'zustand';
import { authAPI } from '../api/client';

const useAuthStore = create((set) => ({
  vendor: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      const { access_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      
      // Fetch vendor info
      const vendorResponse = await authAPI.getCurrentVendor();
      
      set({ 
        vendor: vendorResponse.data, 
        isAuthenticated: true,
        isLoading: false 
      });
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ vendor: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const response = await authAPI.getCurrentVendor();
      set({ 
        vendor: response.data, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      set({ 
        vendor: null, 
        isAuthenticated: false, 
        isLoading: false 
      });
    }
  },
}));

export default useAuthStore;