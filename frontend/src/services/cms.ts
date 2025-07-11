import { api } from './api';

export interface ContentType {
  id: number;
  title: string;
  slug: string;
  description?: string;
  content_type: string;
  status: string;
  body?: string;
  subject_id: number;
  difficulty_level: string;
  estimated_duration?: number;
  learning_objectives: string[];
  prerequisites: number[];
  tags: string[];
  is_featured: boolean;
  is_premium: boolean;
  view_count: number;
  completion_rate: number;
  average_rating: number;
  total_ratings: number;
  version: string;
  author_id: number;
  editor_id?: number;
  published_at?: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  assets: any[];
}

export interface CurriculumType {
  id: number;
  title: string;
  description?: string;
  subject_id: number;
  difficulty_level: string;
  estimated_duration?: number;
  is_sequential: boolean;
  status: string;
  is_premium: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
  items: CurriculumItem[];
}

export interface CurriculumItem {
  id: number;
  content_id: number;
  content_title: string;
  sort_order: number;
  is_required: boolean;
  unlock_criteria: Record<string, any>;
  created_at: string;
}

export interface TemplateType {
  id: number;
  name: string;
  description?: string;
  content_type: string;
  template_body?: string;
  default_metadata: Record<string, any>;
  required_fields: string[];
  is_active: boolean;
  created_by: number;
  created_at: string;
}

export interface Subject {
  id: number;
  name: string;
  code: string;
  description?: string;
  icon?: string;
  color?: string;
  is_active: boolean;
  order: number;
}

export interface ContentCreateData {
  title: string;
  description?: string;
  content_type: string;
  subject_id: number;
  difficulty_level: string;
  estimated_duration?: number;
  learning_objectives: string[];
  prerequisites: number[];
  tags: string[];
  body: string;
  is_premium: boolean;
  slug?: string;
  metadata: Record<string, any>;
  assets?: any[];
}

export interface ContentUpdateData extends Partial<ContentCreateData> {
  change_summary?: string;
}

export interface CurriculumCreateData {
  title: string;
  description?: string;
  subject_id: number;
  difficulty_level: string;
  estimated_duration?: number;
  is_sequential: boolean;
  is_premium: boolean;
  items: Array<{
    content_id: number;
    sort_order: number;
    is_required: boolean;
    unlock_criteria?: Record<string, any>;
  }>;
}

export interface TemplateCreateData {
  name: string;
  description?: string;
  content_type: string;
  template_body?: string;
  default_metadata: Record<string, any>;
  required_fields: string[];
}

export interface SearchFilters {
  content_type?: string;
  subject_id?: number;
  difficulty_level?: string;
  status?: string;
  is_premium?: boolean;
  tags?: string[];
}

export interface SearchResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

class CMSService {
  // Content Management
  async createContent(data: ContentCreateData): Promise<ContentType> {
    const response = await api.post('/cms/content', data);
    return response.data;
  }

  async getContent(id: number): Promise<ContentType> {
    const response = await api.get(`/cms/content/${id}`);
    return response.data;
  }

  async getContentBySlug(slug: string): Promise<ContentType> {
    const response = await api.get(`/cms/content/slug/${slug}`);
    return response.data;
  }

  async updateContent(id: number, data: ContentUpdateData): Promise<ContentType> {
    const response = await api.put(`/cms/content/${id}`, data);
    return response.data;
  }

  async deleteContent(id: number): Promise<void> {
    await api.delete(`/cms/content/${id}`);
  }

  async publishContent(id: number): Promise<ContentType> {
    const response = await api.post(`/cms/content/${id}/publish`);
    return response.data;
  }

  async searchContent(
    query?: string,
    filters?: SearchFilters,
    limit = 20,
    offset = 0
  ): Promise<SearchResponse<ContentType>> {
    const params = new URLSearchParams();
    
    if (query) params.append('q', query);
    if (filters?.content_type) params.append('content_type', filters.content_type);
    if (filters?.subject_id) params.append('subject_id', filters.subject_id.toString());
    if (filters?.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.is_premium !== undefined) params.append('is_premium', filters.is_premium.toString());
    if (filters?.tags) {
      filters.tags.forEach(tag => params.append('tags', tag));
    }
    
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await api.get(`/cms/content?${params}`);
    return response.data;
  }

  async markContentComplete(id: number, timeSpent: number): Promise<void> {
    await api.post(`/cms/content/${id}/complete`, { time_spent: timeSpent });
  }

  async getContentAnalytics(id: number, days = 30): Promise<any> {
    const response = await api.get(`/cms/content/${id}/analytics?days=${days}`);
    return response.data;
  }

  // Curriculum Management
  async createCurriculum(data: CurriculumCreateData): Promise<CurriculumType> {
    const response = await api.post('/cms/curriculum', data);
    return response.data;
  }

  async getCurriculum(id: number): Promise<CurriculumType> {
    const response = await api.get(`/cms/curriculum/${id}`);
    return response.data;
  }

  async updateCurriculum(id: number, data: Partial<CurriculumCreateData>): Promise<CurriculumType> {
    const response = await api.put(`/cms/curriculum/${id}`, data);
    return response.data;
  }

  async deleteCurriculum(id: number): Promise<void> {
    await api.delete(`/cms/curriculum/${id}`);
  }

  async addContentToCurriculum(
    curriculumId: number,
    contentId: number,
    sortOrder: number,
    isRequired = true
  ): Promise<void> {
    await api.post(`/cms/curriculum/${curriculumId}/content/${contentId}`, {
      sort_order: sortOrder,
      is_required: isRequired
    });
  }

  async removeContentFromCurriculum(curriculumId: number, contentId: number): Promise<void> {
    await api.delete(`/cms/curriculum/${curriculumId}/content/${contentId}`);
  }

  async reorderCurriculumItems(
    curriculumId: number,
    itemOrders: Array<{ content_id: number; sort_order: number }>
  ): Promise<void> {
    await api.put(`/cms/curriculum/${curriculumId}/reorder`, itemOrders);
  }

  async getCurriculumProgress(curriculumId: number): Promise<any> {
    const response = await api.get(`/cms/curriculum/${curriculumId}/progress`);
    return response.data;
  }

  async searchCurricula(
    query?: string,
    filters?: Omit<SearchFilters, 'content_type'>,
    limit = 20,
    offset = 0
  ): Promise<SearchResponse<CurriculumType>> {
    const params = new URLSearchParams();
    
    if (query) params.append('q', query);
    if (filters?.subject_id) params.append('subject_id', filters.subject_id.toString());
    if (filters?.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.is_premium !== undefined) params.append('is_premium', filters.is_premium.toString());
    
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await api.get(`/cms/curriculum?${params}`);
    return response.data;
  }

  // Template Management
  async createTemplate(data: TemplateCreateData): Promise<TemplateType> {
    const response = await api.post('/cms/templates', data);
    return response.data;
  }

  async getTemplate(id: number): Promise<TemplateType> {
    const response = await api.get(`/cms/templates/${id}`);
    return response.data;
  }

  async updateTemplate(id: number, data: Partial<TemplateCreateData>): Promise<TemplateType> {
    const response = await api.put(`/cms/templates/${id}`, data);
    return response.data;
  }

  async deleteTemplate(id: number): Promise<void> {
    await api.delete(`/cms/templates/${id}`);
  }

  async getTemplates(filters?: { content_type?: string }, limit = 20, offset = 0): Promise<SearchResponse<TemplateType>> {
    const params = new URLSearchParams();
    
    if (filters?.content_type) params.append('content_type', filters.content_type);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await api.get(`/cms/templates?${params}`);
    return response.data;
  }

  async getTemplatesByType(contentType: string, limit = 20, offset = 0): Promise<SearchResponse<TemplateType>> {
    const response = await api.get(`/cms/templates/type/${contentType}?limit=${limit}&offset=${offset}`);
    return response.data;
  }

  async createContentFromTemplate(
    templateId: number,
    variables: Record<string, any>,
    contentData: Record<string, any>
  ): Promise<ContentType> {
    const response = await api.post(`/cms/templates/${templateId}/content`, {
      variables,
      content_data: contentData
    });
    return response.data;
  }

  async getTemplateVariables(templateId: number): Promise<{ variables: string[] }> {
    const response = await api.get(`/cms/templates/${templateId}/variables`);
    return response.data;
  }

  async previewTemplate(templateId: number, variables: Record<string, any>): Promise<{ rendered: string }> {
    const response = await api.post(`/cms/templates/${templateId}/preview`, variables);
    return response.data;
  }

  async duplicateTemplate(templateId: number, newName: string): Promise<TemplateType> {
    const response = await api.post(`/cms/templates/${templateId}/duplicate`, { new_name: newName });
    return response.data;
  }

  // Version Management
  async getContentVersions(contentId: number): Promise<{ data: any[] }> {
    // This would be implemented when version history endpoint is added
    return { data: [] };
  }

  // Subjects
  async getSubjects(): Promise<{ data: Subject[] }> {
    // This would call a subjects endpoint
    return {
      data: [
        { id: 1, name: 'Mathematics', code: 'MATH', is_active: true, order: 1 },
        { id: 2, name: 'Science', code: 'SCI', is_active: true, order: 2 },
        { id: 3, name: 'English', code: 'ENG', is_active: true, order: 3 },
        { id: 4, name: 'History', code: 'HIST', is_active: true, order: 4 },
      ]
    };
  }

  // Bulk Operations
  async bulkUpdateContent(contentIds: number[], updates: Record<string, any>): Promise<any> {
    const response = await api.post('/cms/content/bulk-update', {
      content_ids: contentIds,
      updates
    });
    return response.data;
  }

  async bulkDeleteContent(contentIds: number[]): Promise<any> {
    const response = await api.post('/cms/content/bulk-delete', {
      content_ids: contentIds
    });
    return response.data;
  }

  // File Upload
  async uploadAsset(file: File, contentId?: number): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (contentId) {
      formData.append('content_id', contentId.toString());
    }

    const response = await api.post('/cms/assets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }

  async deleteAsset(assetId: string): Promise<void> {
    await api.delete(`/cms/assets/${assetId}`);
  }

  // Dashboard Stats
  async getDashboardStats(): Promise<any> {
    const response = await api.get('/cms/dashboard/stats');
    return response.data;
  }
}

export const cmsService = new CMSService();