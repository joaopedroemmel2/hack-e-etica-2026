export type Role = 'ADMIN' | 'GESTOR' | 'COLABORADOR';
export type ProjectStatus = 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  isActive?: boolean;
  weeklyCapacityHours?: number;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface DashboardData {
  summary: {
    activeProjects: number;
    totalTasks: number;
    completedTasks: number;
    overdueTasks: number;
    completionPercentage: number;
    loggedHours: number;
    overtimeHours: number;
    overloadedUsers: number;
  };
  taskCharts: {
    byStatus: Array<{ status: TaskStatus; value: number }>;
    byPriority: Array<{ priority: TaskPriority; value: number }>;
  };
  hoursChart: Array<{ date: string; hours: number }>;
  productivityChart: Array<{ date: string; createdTasks: number; completedTasks: number }>;
  workload: Array<{
    user: Pick<User, 'id' | 'name' | 'email'>;
    capacityHours: number;
    committedHours: number;
    utilizationPercentage: number;
    overloaded: boolean;
  }>;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  teamId: string;
  managerId: string | null;
  startDate: string | null;
  dueDate: string | null;
  team: { id: string; name: string };
  manager: Pick<User, 'id' | 'name' | 'email'> | null;
  tasksCount: number;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  projectId: string;
  assigneeId: string | null;
  dueDate: string | null;
  estimatedHours: number | null;
  loggedMinutes: number;
  project: { id: string; name: string; teamId: string };
  assignee: Pick<User, 'id' | 'name' | 'email'> | null;
}

export interface Paginated<T> {
  data: T[];
  meta: { page: number; limit: number; total: number; totalPages: number };
}
