import axios from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 
                     (window.location.hostname === 'localhost' 
                        ? 'http://localhost:8000' 
                        : 'https://meih-movies-api.onrender.com');

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Simple in-memory cache
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

function getCachedData<T>(key: string): T | null {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data as T;
  }
  cache.delete(key);
  return null;
}

function setCachedData<T>(key: string, data: T): void {
  cache.set(key, { data, timestamp: Date.now() });
}

export interface ContentItem {
    id: string;
    title: string;
    poster: string;
    type: 'movie' | 'series';
    duration?: string;
}

export interface Episode {
    id: string;
    title: string;
    episode: number;
    url: string;
}

export interface Server {
    name: string;
    url: string;
    type?: 'video' | 'iframe';
}

export interface Download {
    quality: string;
    url: string;
}

export interface Details {
    title: string;
    description: string;
    poster: string;
    type: 'movie' | 'series';
    episodes: Episode[];
    servers: Server[];
    download_links: Download[];
    current_episode?: {
        id: string;
        title: string;
    };
    error?: string;
    message?: string;
}

export const fetchLatest = async (page: number = 1) => {
  const cacheKey = `latest_${page}`;
  const cached = getCachedData<ContentItem[]>(cacheKey);
  if (cached) return cached;
  
  const data = (await api.get<ContentItem[]>(`/content/latest?page=${page}`)).data;
  setCachedData(cacheKey, data);
  return data;
};
export const fetchDetails = async (id: string) => {
  const cacheKey = `details_${id}`;
  const cached = getCachedData<Details>(cacheKey);
  if (cached) return cached;
  
  const data = (await api.get<Details>(`/content/details/${id}`)).data;
  setCachedData(cacheKey, data);
  return data;
};
export const searchItems = async (query: string) => {
  const cacheKey = `search_${query}`;
  const cached = getCachedData<ContentItem[]>(cacheKey);
  if (cached) return cached;
  
  const data = (await api.get<ContentItem[]>(`/content/search?q=${query}`)).data;
  setCachedData(cacheKey, data);
  return data;
};
export const fetchByCategory = async (catId: string, page: number = 1) => {
  const cacheKey = `category_${catId}_${page}`;
  const cached = getCachedData<ContentItem[]>(cacheKey);
  if (cached) return cached;
  
  const data = (await api.get<ContentItem[]>(`/content/group/${catId}?page=${page}`)).data;
  setCachedData(cacheKey, data);
  return data;
};
