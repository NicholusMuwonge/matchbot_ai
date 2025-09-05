# State Management Implementation Tasks

This document provides step-by-step guides for common state management tasks using Zustand in our React application. Reference this during development to ensure consistent implementation patterns.

## Installation and Setup Tasks

### Task 1: Install and Configure Zustand

**Step 1: Install Dependencies**
```bash
npm install zustand
npm install --save-dev @types/node  # For TypeScript support
```

**Step 2: Create Store Utils**
```typescript
// src/shared/utils/storeUtils.ts
import { StoreApi, UseBoundStore } from 'zustand';

type WithSelectors<S> = S extends { getState: () => infer T }
  ? S & { use: { [K in keyof T]: () => T[K] } }
  : never;

export const createSelectors = <S extends UseBoundStore<StoreApi<object>>>(
  _store: S,
) => {
  const store = _store as WithSelectors<typeof _store>;
  store.use = {};
  for (const k of Object.keys(store.getState())) {
    (store.use as any)[k] = () => store((s) => s[k as keyof typeof s]);
  }
  return store;
};
```

**Step 3: Configure DevTools (Development)**
```typescript
// src/shared/utils/devtools.ts
export const devtoolsOptions = {
  enabled: process.env.NODE_ENV === 'development',
  name: 'Matchbot-Store', // Will appear in Redux DevTools
};
```

### Task 2: Set Up Store Directory Structure

Create the following directory structure:

```
src/
├── shared/
│   └── stores/
│       ├── appStore.ts          # Global app state
│       ├── themeStore.ts        # Theme and UI preferences
│       └── notificationStore.ts # Global notifications
└── features/
    ├── reconciliation/
    │   └── stores/
    │       ├── reconciliationStore.ts
    │       └── taskFiltersStore.ts
    ├── authentication/
    │   └── stores/
    │       └── authStore.ts
    └── administration/
        └── stores/
            └── adminStore.ts
```

## Feature Store Creation Tasks

### Task 3: Create a Basic Feature Store

**Template for New Feature Store:**

```typescript
// features/[feature-name]/stores/[feature]Store.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { devtoolsOptions } from 'shared/utils/devtools';

// 1. Define your state interface
interface [Feature]Store {
  // State properties
  selectedId: string | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setSelected: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
  
  // Computed properties (as functions)
  hasSelection: () => boolean;
}

// 2. Define initial state
const initialState = {
  selectedId: null,
  loading: false,
  error: null,
};

// 3. Create the store
export const use[Feature]Store = create<[Feature]Store>()(
  devtools(
    (set, get) => ({
      ...initialState,
      
      // Actions
      setSelected: (id) => set({ selectedId: id }, false, 'setSelected'),
      setLoading: (loading) => set({ loading }, false, 'setLoading'),
      setError: (error) => set({ error }, false, 'setError'),
      reset: () => set(initialState, false, 'reset'),
      
      // Computed properties
      hasSelection: () => get().selectedId !== null,
    }),
    { ...devtoolsOptions, name: '[Feature]Store' }
  )
);
```

**Example: Reconciliation Store**

```typescript
// features/reconciliation/stores/reconciliationStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { devtoolsOptions } from 'shared/utils/devtools';

interface ReconciliationStore {
  // Selection State
  selectedTaskId: string | null;
  bulkSelectionMode: boolean;
  selectedTaskIds: string[];
  
  // View State  
  viewMode: 'grid' | 'list' | 'kanban';
  showFilters: boolean;
  
  // UI State
  sidebarOpen: boolean;
  
  // Actions
  setSelectedTask: (taskId: string | null) => void;
  toggleBulkSelection: () => void;
  toggleTaskSelection: (taskId: string) => void;
  clearSelection: () => void;
  setViewMode: (mode: 'grid' | 'list' | 'kanban') => void;
  setShowFilters: (show: boolean) => void;
  setSidebarOpen: (open: boolean) => void;
  
  // Computed
  selectionCount: () => number;
  hasSelection: () => boolean;
}

const initialState = {
  selectedTaskId: null,
  bulkSelectionMode: false,
  selectedTaskIds: [],
  viewMode: 'grid' as const,
  showFilters: false,
  sidebarOpen: true,
};

export const useReconciliationStore = create<ReconciliationStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setSelectedTask: (taskId) => set(
          { selectedTaskId: taskId },
          false,
          'setSelectedTask'
        ),
        
        toggleBulkSelection: () => set(
          (state) => ({
            bulkSelectionMode: !state.bulkSelectionMode,
            selectedTaskIds: state.bulkSelectionMode ? [] : state.selectedTaskIds
          }),
          false,
          'toggleBulkSelection'
        ),
        
        toggleTaskSelection: (taskId) => set(
          (state) => ({
            selectedTaskIds: state.selectedTaskIds.includes(taskId)
              ? state.selectedTaskIds.filter(id => id !== taskId)
              : [...state.selectedTaskIds, taskId]
          }),
          false,
          'toggleTaskSelection'
        ),
        
        clearSelection: () => set(
          { selectedTaskIds: [], bulkSelectionMode: false },
          false,
          'clearSelection'
        ),
        
        setViewMode: (mode) => set({ viewMode: mode }, false, 'setViewMode'),
        setShowFilters: (show) => set({ showFilters: show }, false, 'setShowFilters'),
        setSidebarOpen: (open) => set({ sidebarOpen: open }, false, 'setSidebarOpen'),
        
        // Computed properties
        selectionCount: () => get().selectedTaskIds.length,
        hasSelection: () => get().selectedTaskIds.length > 0,
      }),
      {
        name: 'reconciliation-store',
        partialize: (state) => ({
          viewMode: state.viewMode,
          showFilters: state.showFilters,
          sidebarOpen: state.sidebarOpen,
        }), // Only persist UI preferences
      }
    ),
    { ...devtoolsOptions, name: 'ReconciliationStore' }
  )
);
```

### Task 4: Create Global App Store

```typescript
// src/shared/stores/appStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { devtoolsOptions } from 'shared/utils/devtools';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  avatar?: string;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface AppStore {
  // User State
  user: User | null;
  isAuthenticated: boolean;
  
  // App State
  isOnline: boolean;
  notifications: Notification[];
  
  // Actions
  setUser: (user: User | null) => void;
  setOnlineStatus: (online: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  
  // Computed
  unreadNotificationCount: () => number;
}

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        isAuthenticated: false,
        isOnline: true,
        notifications: [],
        
        setUser: (user) => set(
          { user, isAuthenticated: !!user },
          false,
          'setUser'
        ),
        
        setOnlineStatus: (online) => set(
          { isOnline: online },
          false,
          'setOnlineStatus'
        ),
        
        addNotification: (notification) => set(
          (state) => ({
            notifications: [
              {
                ...notification,
                id: crypto.randomUUID(),
                timestamp: new Date(),
                read: false,
              },
              ...state.notifications,
            ].slice(0, 50) // Keep only last 50 notifications
          }),
          false,
          'addNotification'
        ),
        
        markNotificationRead: (id) => set(
          (state) => ({
            notifications: state.notifications.map(n =>
              n.id === id ? { ...n, read: true } : n
            )
          }),
          false,
          'markNotificationRead'
        ),
        
        removeNotification: (id) => set(
          (state) => ({
            notifications: state.notifications.filter(n => n.id !== id)
          }),
          false,
          'removeNotification'
        ),
        
        clearAllNotifications: () => set(
          { notifications: [] },
          false,
          'clearAllNotifications'
        ),
        
        unreadNotificationCount: () => 
          get().notifications.filter(n => !n.read).length,
      }),
      {
        name: 'app-store',
        partialize: (state) => ({
          user: state.user,
          // Don't persist notifications or online status
        }),
      }
    ),
    { ...devtoolsOptions, name: 'AppStore' }
  )
);
```

## Component Integration Tasks

### Task 5: Integrate Store with Components

**Basic Component Usage:**

```typescript
// features/reconciliation/components/ReconciliationDashboard.tsx
import React from 'react';
import { Box, HStack, VStack, Button, useColorModeValue } from '@chakra-ui/react';
import { useReconciliationStore } from '../stores/reconciliationStore';

export const ReconciliationDashboard: React.FC = () => {
  // 1. Select only what you need to prevent unnecessary re-renders
  const selectedTaskId = useReconciliationStore(state => state.selectedTaskId);
  const viewMode = useReconciliationStore(state => state.viewMode);
  const showFilters = useReconciliationStore(state => state.showFilters);
  
  // 2. Select actions
  const { setViewMode, setShowFilters } = useReconciliationStore();
  
  // 3. Chakra UI integration
  const bg = useColorModeValue('white', 'gray.800');
  
  return (
    <VStack spacing={4} align="stretch" bg={bg} p={6}>
      <HStack justify="space-between">
        <HStack>
          <Button
            size="sm"
            variant={viewMode === 'grid' ? 'solid' : 'ghost'}
            onClick={() => setViewMode('grid')}
          >
            Grid
          </Button>
          <Button
            size="sm"
            variant={viewMode === 'list' ? 'solid' : 'ghost'}
            onClick={() => setViewMode('list')}
          >
            List
          </Button>
          <Button
            size="sm"
            variant={viewMode === 'kanban' ? 'solid' : 'ghost'}
            onClick={() => setViewMode('kanban')}
          >
            Kanban
          </Button>
        </HStack>
        
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? 'Hide' : 'Show'} Filters
        </Button>
      </HStack>
      
      <Box>
        {selectedTaskId ? (
          <p>Selected task: {selectedTaskId}</p>
        ) : (
          <p>No task selected</p>
        )}
      </Box>
    </VStack>
  );
};
```

**Performance-Optimized Component:**

```typescript
// Use selectors for better performance
import { createSelectors } from 'shared/utils/storeUtils';

const reconciliationStore = useReconciliationStore;
const useReconciliationSelectors = createSelectors(reconciliationStore);

export const OptimizedTaskCard: React.FC<{ taskId: string }> = ({ taskId }) => {
  // This will only re-render when selectedTaskId changes
  const selectedTaskId = useReconciliationSelectors.use.selectedTaskId();
  const setSelectedTask = useReconciliationSelectors.use.setSelectedTask();
  
  const isSelected = selectedTaskId === taskId;
  
  return (
    <Box
      p={4}
      border="1px"
      borderColor={isSelected ? 'blue.500' : 'gray.200'}
      borderRadius="md"
      cursor="pointer"
      onClick={() => setSelectedTask(taskId)}
    >
      Task {taskId} {isSelected && '(Selected)'}
    </Box>
  );
};
```

### Task 6: Integrate Store with Services

```typescript
// features/reconciliation/services/ReconciliationService.ts
import { useReconciliationStore } from '../stores/reconciliationStore';
import { useAppStore } from 'shared/stores/appStore';

export class ReconciliationService {
  constructor(
    private apiClient: ApiClient,
    private notificationService: NotificationService
  ) {}

  async createTask(config: ReconciliationConfig): Promise<ReconciliationTask> {
    // Get store actions
    const { setSelectedTask } = useReconciliationStore.getState();
    const { addNotification } = useAppStore.getState();
    
    try {
      const task = await this.apiClient.post('/reconciliation/tasks', config);
      
      // Update store
      setSelectedTask(task.id);
      
      // Add success notification
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Reconciliation task created successfully',
      });
      
      return task;
    } catch (error) {
      // Add error notification
      addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to create reconciliation task',
      });
      throw error;
    }
  }

  async deleteTask(taskId: string): Promise<void> {
    const { selectedTaskId, setSelectedTask, selectedTaskIds, clearSelection } = 
      useReconciliationStore.getState();
    const { addNotification } = useAppStore.getState();
    
    try {
      await this.apiClient.delete(`/reconciliation/tasks/${taskId}`);
      
      // Clear selection if deleted task was selected
      if (selectedTaskId === taskId) {
        setSelectedTask(null);
      }
      
      // Remove from bulk selection
      if (selectedTaskIds.includes(taskId)) {
        clearSelection();
      }
      
      addNotification({
        type: 'success',
        title: 'Task Deleted',
        message: 'Task deleted successfully',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Delete Failed',
        message: 'Failed to delete task',
      });
      throw error;
    }
  }
}
```

### Task 7: Integrate with TanStack Query

```typescript
// features/reconciliation/hooks/useReconciliationTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useReconciliationStore } from '../stores/reconciliationStore';
import { ReconciliationService } from '../services/ReconciliationService';

export const useReconciliationTasks = (filters?: TaskFilters) => {
  const queryClient = useQueryClient();
  const reconciliationService = new ReconciliationService(/* deps */);
  
  // TanStack Query for server state
  const {
    data: tasks,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['reconciliation-tasks', filters],
    queryFn: () => reconciliationService.fetchTasks(filters),
  });

  // Zustand for client state
  const selectedTaskId = useReconciliationStore(state => state.selectedTaskId);
  const setSelectedTask = useReconciliationStore(state => state.setSelectedTask);

  // Combine server and client state
  const selectedTask = tasks?.find(task => task.id === selectedTaskId);

  // Mutations that update both server and client state
  const createTaskMutation = useMutation({
    mutationFn: reconciliationService.createTask,
    onSuccess: (newTask) => {
      // Update server state cache
      queryClient.invalidateQueries({ queryKey: ['reconciliation-tasks'] });
      
      // Update client state
      setSelectedTask(newTask.id);
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: reconciliationService.deleteTask,
    onMutate: async (taskId) => {
      // Optimistic update: remove from client state immediately
      if (selectedTaskId === taskId) {
        setSelectedTask(null);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-tasks'] });
    },
    onError: (error, taskId) => {
      // Revert optimistic update on error
      // Could restore previous selection here
    },
  });

  return {
    // Server state
    tasks,
    isLoading,
    error,
    
    // Client state
    selectedTask,
    selectedTaskId,
    
    // Actions
    createTask: createTaskMutation.mutate,
    deleteTask: deleteTaskMutation.mutate,
    setSelectedTask,
    
    // Status
    isCreating: createTaskMutation.isPending,
    isDeleting: deleteTaskMutation.isPending,
  };
};
```

## Testing Tasks

### Task 8: Unit Test Stores

```typescript
// features/reconciliation/stores/reconciliationStore.test.ts
import { act, renderHook } from '@testing-library/react';
import { useReconciliationStore } from './reconciliationStore';

describe('ReconciliationStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useReconciliationStore.setState({
      selectedTaskId: null,
      bulkSelectionMode: false,
      selectedTaskIds: [],
      viewMode: 'grid',
      showFilters: false,
      sidebarOpen: true,
    });
  });

  describe('Task Selection', () => {
    it('should set selected task', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      act(() => {
        result.current.setSelectedTask('task-123');
      });
      
      expect(result.current.selectedTaskId).toBe('task-123');
    });

    it('should clear selected task', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      // First select a task
      act(() => {
        result.current.setSelectedTask('task-123');
      });
      
      // Then clear it
      act(() => {
        result.current.setSelectedTask(null);
      });
      
      expect(result.current.selectedTaskId).toBeNull();
    });
  });

  describe('Bulk Selection', () => {
    it('should toggle bulk selection mode', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      act(() => {
        result.current.toggleBulkSelection();
      });
      
      expect(result.current.bulkSelectionMode).toBe(true);
      
      act(() => {
        result.current.toggleBulkSelection();
      });
      
      expect(result.current.bulkSelectionMode).toBe(false);
    });

    it('should toggle task in bulk selection', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      act(() => {
        result.current.toggleTaskSelection('task-1');
        result.current.toggleTaskSelection('task-2');
      });
      
      expect(result.current.selectedTaskIds).toEqual(['task-1', 'task-2']);
      expect(result.current.selectionCount()).toBe(2);
      expect(result.current.hasSelection()).toBe(true);
      
      // Remove one task
      act(() => {
        result.current.toggleTaskSelection('task-1');
      });
      
      expect(result.current.selectedTaskIds).toEqual(['task-2']);
      expect(result.current.selectionCount()).toBe(1);
    });

    it('should clear all selections', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      // Set up some selections
      act(() => {
        result.current.toggleTaskSelection('task-1');
        result.current.toggleTaskSelection('task-2');
        result.current.toggleBulkSelection();
      });
      
      // Clear everything
      act(() => {
        result.current.clearSelection();
      });
      
      expect(result.current.selectedTaskIds).toEqual([]);
      expect(result.current.bulkSelectionMode).toBe(false);
      expect(result.current.hasSelection()).toBe(false);
    });
  });

  describe('View Mode', () => {
    it('should change view mode', () => {
      const { result } = renderHook(() => useReconciliationStore());
      
      act(() => {
        result.current.setViewMode('list');
      });
      
      expect(result.current.viewMode).toBe('list');
      
      act(() => {
        result.current.setViewMode('kanban');
      });
      
      expect(result.current.viewMode).toBe('kanban');
    });
  });
});
```

### Task 9: Integration Test with Components

```typescript
// features/reconciliation/components/ReconciliationDashboard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { ReconciliationDashboard } from './ReconciliationDashboard';
import { useReconciliationStore } from '../stores/reconciliationStore';

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ChakraProvider>
    {children}
  </ChakraProvider>
);

describe('ReconciliationDashboard', () => {
  beforeEach(() => {
    // Reset store
    useReconciliationStore.getState().setViewMode('grid');
    useReconciliationStore.getState().setShowFilters(false);
  });

  it('should change view mode when buttons are clicked', () => {
    render(<ReconciliationDashboard />, { wrapper: TestWrapper });
    
    const listButton = screen.getByText('List');
    fireEvent.click(listButton);
    
    // Check that store was updated
    expect(useReconciliationStore.getState().viewMode).toBe('list');
  });

  it('should toggle filters when filter button is clicked', () => {
    render(<ReconciliationDashboard />, { wrapper: TestWrapper });
    
    const filterButton = screen.getByText('Show Filters');
    fireEvent.click(filterButton);
    
    expect(useReconciliationStore.getState().showFilters).toBe(true);
    expect(screen.getByText('Hide Filters')).toBeInTheDocument();
  });

  it('should display selected task when one is selected', () => {
    // Pre-select a task
    useReconciliationStore.getState().setSelectedTask('task-123');
    
    render(<ReconciliationDashboard />, { wrapper: TestWrapper });
    
    expect(screen.getByText('Selected task: task-123')).toBeInTheDocument();
  });
});
```

## Advanced Tasks

### Task 10: Add Middleware for Persistence and DevTools

```typescript
// features/reconciliation/stores/advancedReconciliationStore.ts
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface AdvancedStore {
  tasks: ReconciliationTask[];
  filters: TaskFilters;
  preferences: UserPreferences;
  
  // Actions using Immer for immutability
  addTask: (task: ReconciliationTask) => void;
  updateTask: (id: string, updates: Partial<ReconciliationTask>) => void;
  removeTask: (id: string) => void;
  setFilters: (filters: TaskFilters) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
}

export const useAdvancedStore = create<AdvancedStore>()(
  // DevTools
  devtools(
    // Persistence
    persist(
      // Subscriptions
      subscribeWithSelector(
        // Immer for immutability
        immer((set) => ({
          tasks: [],
          filters: {},
          preferences: { theme: 'light', language: 'en' },
          
          addTask: (task) => set((state) => {
            state.tasks.push(task); // Immer allows "mutations"
          }),
          
          updateTask: (id, updates) => set((state) => {
            const taskIndex = state.tasks.findIndex(t => t.id === id);
            if (taskIndex !== -1) {
              Object.assign(state.tasks[taskIndex], updates);
            }
          }),
          
          removeTask: (id) => set((state) => {
            state.tasks = state.tasks.filter(t => t.id !== id);
          }),
          
          setFilters: (filters) => set((state) => {
            state.filters = filters;
          }),
          
          updatePreferences: (preferences) => set((state) => {
            Object.assign(state.preferences, preferences);
          }),
        }))
      ),
      {
        name: 'advanced-reconciliation-store',
        partialize: (state) => ({
          preferences: state.preferences,
          filters: state.filters,
        }),
      }
    ),
    { name: 'AdvancedReconciliationStore' }
  )
);

// Add subscriptions for side effects
useAdvancedStore.subscribe(
  (state) => state.preferences.theme,
  (theme) => {
    // Update document theme
    document.documentElement.setAttribute('data-theme', theme);
  }
);

// Analytics subscription
useAdvancedStore.subscribe(
  (state) => state.filters,
  (filters) => {
    // Track filter usage
    analytics.track('filters_changed', { filters });
  }
);
```

### Task 11: Create Store Slices for Large Stores

```typescript
// features/reconciliation/stores/slices/tasksSlice.ts
import { StateCreator } from 'zustand';

export interface TasksSlice {
  tasks: ReconciliationTask[];
  loading: boolean;
  error: string | null;
  
  setTasks: (tasks: ReconciliationTask[]) => void;
  addTask: (task: ReconciliationTask) => void;
  updateTask: (id: string, updates: Partial<ReconciliationTask>) => void;
  removeTask: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const createTasksSlice: StateCreator<
  TasksSlice & FiltersSlice & UISlice, // Combined store type
  [],
  [],
  TasksSlice
> = (set, get) => ({
  tasks: [],
  loading: false,
  error: null,
  
  setTasks: (tasks) => set({ tasks }),
  
  addTask: (task) => set((state) => ({
    tasks: [...state.tasks, task]
  })),
  
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map(task =>
      task.id === id ? { ...task, ...updates } : task
    )
  })),
  
  removeTask: (id) => set((state) => ({
    tasks: state.tasks.filter(task => task.id !== id)
  })),
  
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
});

// features/reconciliation/stores/slices/filtersSlice.ts
export interface FiltersSlice {
  filters: TaskFilters;
  setFilters: (filters: TaskFilters) => void;
  clearFilters: () => void;
}

export const createFiltersSlice: StateCreator<
  TasksSlice & FiltersSlice & UISlice,
  [],
  [],
  FiltersSlice
> = (set) => ({
  filters: {},
  
  setFilters: (filters) => set({ filters }),
  clearFilters: () => set({ filters: {} }),
});

// features/reconciliation/stores/reconciliationStore.ts - Combined
type ReconciliationStore = TasksSlice & FiltersSlice & UISlice;

export const useReconciliationStore = create<ReconciliationStore>()(
  devtools(
    persist(
      (...a) => ({
        ...createTasksSlice(...a),
        ...createFiltersSlice(...a),
        ...createUISlice(...a),
      }),
      {
        name: 'reconciliation-store',
        partialize: (state) => ({
          filters: state.filters,
          viewMode: state.viewMode,
        }),
      }
    ),
    { name: 'ReconciliationStore' }
  )
);
```

This task-oriented guide provides specific, actionable steps for implementing Zustand in your React application with TanStack Query, Chakra UI, and Tailwind CSS. Each task includes complete code examples that follow the established patterns and can be directly implemented in your project.