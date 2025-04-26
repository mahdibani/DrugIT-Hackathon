import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8123",
  timeout: 30000, // 30 seconds timeout
});

// Add response interceptors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      return Promise.reject(new Error("Request timed out. Please try again."));
    }
    return Promise.reject(error);
  }
);

export default api;