# State Management with Zustand

## Executive Summary

**Recommendation: Zustand** for client-side state management in our TanStack + Chakra UI + Tailwind React application.

**Key Benefits:**
- **Lightweight**: Only 2.9kb bundle size, perfect for MVP to enterprise scaling
- **Perfect Integration**: Complements TanStack Query without overlap
- **Zero Conflicts**: Works seamlessly with Chakra UI and Tailwind CSS
- **TypeScript First**: Excellent TypeScript support out of the box
- **Feature Module Friendly**: Fits perfectly with our modular architecture
- **Simple Testing**: Stores are just functions, easy to unit test

## Technology Stack Integration

### TanStack Query + Zustand Division of Responsibility

```
┌─────────────────┬─────────────────────────────────┐
│   State Type    │          Managed By             │
├─────────────────┼─────────────────────────────────┤
│ Server State    │ TanStack Query                  │
│ API Data        │ • Data fetching                 │
│ Caching         │ • Background updates            │
│ Synchronization │ • Error & loading states        │
├─────────────────┼─────────────────────────────────┤
│ Client State    │ Zustand                         │
│ UI State        │ • Form data                     │
│ User Preferences│ • Theme settings                │
│ App Settings    │ • Navigation state              │
│ Temporary Data  │ • Modal/drawer state            │
└─────────────────┴─────────────────────────────────┘
```

### Integration Example

```typescript
// TanStack Query for server state
const { data: tasks, mutate } = useQuery({
  queryKey: ['reconciliation-tasks'],
  queryFn: reconciliationService.fetchTasks
});

// Zustand for client state
const { selectedTaskId, setSelectedTask } = useReconciliationStore();

// Perfect separation: server data + client UI state
const selectedTask = tasks?.find(task => task.id === selectedTaskId);
```

### Chakra UI Integration

Zustand complements Chakra UI by managing application-level state while Chakra handles component-level state:

```typescript
// Zustand store for theme preferences
interface ThemeStore {
  colorMode: 'light' | 'dark';
  primaryColor: string;
  fontSize: 'sm' | 'md' | 'lg';
  setColorMode: (mode: 'light' | 'dark') => void;
  setPrimaryColor: (color: string) => void;
  setFontSize: (size: 'sm' | 'md' | 'lg') => void;
}

export const useThemeStore = create<ThemeStore>((set) => ({
  colorMode: 'light',
  primaryColor: '#2463eb',
  fontSize: 'md',
  setColorMode: (mode) => set({ colorMode: mode }),
  setPrimaryColor: (color) => set({ primaryColor: color }),
  setFontSize: (size) => set({ fontSize: size }),
}));

// Usage with Chakra UI
const { colorMode, setColorMode } = useThemeStore();
const { setColorMode: setChakraColorMode } = useColorMode();

// Sync Zustand with Chakra UI
useEffect(() => {
  setChakraColorMode(colorMode);
}, [colorMode, setChakraColorMode]);
```

### Tailwind CSS Integration

Zustand can manage dynamic Tailwind classes and responsive behavior:

```typescript
interface LayoutStore {
  sidebarCollapsed: boolean;
  screenSize: 'sm' | 'md' | 'lg' | 'xl';
  toggleSidebar: () => void;
  setScreenSize: (size: 'sm' | 'md' | 'lg' | 'xl') => void;
}

export const useLayoutStore = create<LayoutStore>((set) => ({
  sidebarCollapsed: false,
  screenSize: 'lg',
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setScreenSize: (size) => set({ screenSize: size }),
}));

// Dynamic Tailwind classes
const { sidebarCollapsed, screenSize } = useLayoutStore();
const sidebarClasses = `
  ${sidebarCollapsed ? 'w-16' : 'w-64'}
  ${screenSize === 'sm' ? 'absolute' : 'relative'}
  transition-all duration-300
`;
```

## Architecture Integration

### Feature Module Store Structure

Following our modular architecture, each feature can have its own store:

```
features/reconciliation/
├── components/
├── services/
├── models/
├── hooks/
├── stores/
│   ├── reconciliationStore.ts     # Main feature store
│   ├── taskFiltersStore.ts        # Sub-feature store
│   └── conflictResolutionStore.ts # Sub-feature store
└── types/
```

### Feature Store Example

```typescript
// features/reconciliation/stores/reconciliationStore.ts
interface ReconciliationStore {
  // State
  selectedTaskId: string | null;
  viewMode: 'grid' | 'list' | 'kanban';
  bulkSelectionMode: boolean;
  selectedTaskIds: string[];
  
  // UI State
  showFilters: boolean;
  showBulkActions: boolean;
  
  // Actions
  setSelectedTask: (taskId: string | null) => void;
  setViewMode: (mode: 'grid' | 'list' | 'kanban') => void;
  toggleBulkSelection: () => void;
  toggleTaskSelection: (taskId: string) => void;
  clearSelection: () => void;
  setShowFilters: (show: boolean) => void;
  setShowBulkActions: (show: boolean) => void;
  
  // Computed
  hasSelection: () => boolean;
  selectionCount: () => number;
}

export const useReconciliationStore = create<ReconciliationStore>((set, get) => ({
  selectedTaskId: null,
  viewMode: 'grid',
  bulkSelectionMode: false,
  selectedTaskIds: [],
  showFilters: false,
  showBulkActions: false,
  
  setSelectedTask: (taskId) => set({ selectedTaskId: taskId }),
  setViewMode: (mode) => set({ viewMode: mode }),
  toggleBulkSelection: () => set((state) => ({ 
    bulkSelectionMode: !state.bulkSelectionMode,
    selectedTaskIds: state.bulkSelectionMode ? [] : state.selectedTaskIds
  })),
  toggleTaskSelection: (taskId) => set((state) => ({
    selectedTaskIds: state.selectedTaskIds.includes(taskId)
      ? state.selectedTaskIds.filter(id => id !== taskId)
      : [...state.selectedTaskIds, taskId]
  })),
  clearSelection: () => set({ selectedTaskIds: [], bulkSelectionMode: false }),
  setShowFilters: (show) => set({ showFilters: show }),
  setShowBulkActions: (show) => set({ showBulkActions: show }),
  
  hasSelection: () => get().selectedTaskIds.length > 0,
  selectionCount: () => get().selectedTaskIds.length,
}));
```

### Global Stores

For cross-cutting concerns, create global stores:

```typescript
// shared/stores/appStore.ts
interface AppStore {
  user: User | null;
  notifications: Notification[];
  isOnline: boolean;
  
  setUser: (user: User | null) => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  setOnlineStatus: (online: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  user: null,
  notifications: [],
  isOnline: true,
  
  setUser: (user) => set({ user }),
  addNotification: (notification) => set((state) => ({
    notifications: [...state.notifications, notification]
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  })),
  setOnlineStatus: (online) => set({ isOnline: online }),
}));
```

## Service Layer Integration

Integrate Zustand stores with the service layer:

```typescript
// features/reconciliation/services/ReconciliationService.ts
export class ReconciliationService {
  constructor(
    private apiClient: ApiClient,
    private notificationService: NotificationService
  ) {}

  async createTask(config: ReconciliationConfig): Promise<ReconciliationTask> {
    try {
      // Update store to show loading state
      useReconciliationStore.getState().setCreating(true);
      
      const task = await this.apiClient.post('/reconciliation/tasks', config);
      
      // Update store with new task
      useReconciliationStore.getState().setSelectedTask(task.id);
      
      this.notificationService.success('Task created successfully');
      return task;
    } catch (error) {
      this.notificationService.error('Failed to create task');
      throw error;
    } finally {
      useReconciliationStore.getState().setCreating(false);
    }
  }
  
  async deleteTask(taskId: string): Promise<void> {
    const { selectedTaskId, setSelectedTask, selectedTaskIds, clearSelection } = 
      useReconciliationStore.getState();
    
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
      
      this.notificationService.success('Task deleted');
    } catch (error) {
      this.notificationService.error('Failed to delete task');
      throw error;
    }
  }
}
```

## MVP to Enterprise Scaling

### Phase 1: MVP (Basic Zustand)

```typescript
// Simple store without middleware
export const useReconciliationStore = create<ReconciliationStore>((set) => ({
  selectedTaskId: null,
  setSelectedTask: (taskId) => set({ selectedTaskId: taskId }),
}));
```

### Phase 2: Growth (Add Middleware)

```typescript
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';

export const useReconciliationStore = create<ReconciliationStore>()(
  devtools(
    persist(
      subscribeWithSelector((set, get) => ({
        selectedTaskId: null,
        viewMode: 'grid',
        setSelectedTask: (taskId) => set({ selectedTaskId: taskId }),
        setViewMode: (mode) => set({ viewMode: mode }),
      })),
      {
        name: 'reconciliation-store',
        partialize: (state) => ({ viewMode: state.viewMode }), // Only persist certain fields
      }
    ),
    { name: 'ReconciliationStore' }
  )
);

// Add subscriptions for side effects
useReconciliationStore.subscribe(
  (state) => state.selectedTaskId,
  (selectedTaskId) => {
    // Analytics tracking
    analytics.track('task_selected', { taskId: selectedTaskId });
  }
);
```

### Phase 3: Enterprise (Advanced Patterns)

```typescript
import { createSelectors } from 'shared/utils/storeUtils';

// Create selectors for performance
const reconciliationStore = create<ReconciliationStore>()(/*...*/);
export const useReconciliationStore = createSelectors(reconciliationStore);

// Usage with selectors (prevents unnecessary re-renders)
const selectedTaskId = useReconciliationStore.use.selectedTaskId();
const setSelectedTask = useReconciliationStore.use.setSelectedTask();

// Store slicing for large stores
interface ReconciliationStoreSlice {
  tasks: ReconciliationTask[];
  filters: TaskFilters;
  ui: UIState;
}

const createTasksSlice: StateCreator<ReconciliationStore, [], [], TasksSlice> = (set) => ({
  tasks: [],
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
});

const createFiltersSlice: StateCreator<ReconciliationStore, [], [], FiltersSlice> = (set) => ({
  filters: {},
  setFilters: (filters) => set({ filters }),
});

export const useReconciliationStore = create<ReconciliationStore>()((...a) => ({
  ...createTasksSlice(...a),
  ...createFiltersSlice(...a),
}));
```

## Testing Strategies

### Unit Testing Stores

```typescript
// features/reconciliation/stores/reconciliationStore.test.ts
import { renderHook, act } from '@testing-library/react';
import { useReconciliationStore } from './reconciliationStore';

describe('ReconciliationStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useReconciliationStore.setState({
      selectedTaskId: null,
      viewMode: 'grid',
      selectedTaskIds: [],
    });
  });

  it('should select a task', () => {
    const { result } = renderHook(() => useReconciliationStore());
    
    act(() => {
      result.current.setSelectedTask('task-123');
    });
    
    expect(result.current.selectedTaskId).toBe('task-123');
  });

  it('should toggle bulk selection mode', () => {
    const { result } = renderHook(() => useReconciliationStore());
    
    act(() => {
      result.current.toggleBulkSelection();
    });
    
    expect(result.current.bulkSelectionMode).toBe(true);
  });

  it('should compute selection count correctly', () => {
    const { result } = renderHook(() => useReconciliationStore());
    
    act(() => {
      result.current.toggleTaskSelection('task-1');
      result.current.toggleTaskSelection('task-2');
    });
    
    expect(result.current.selectionCount()).toBe(2);
    expect(result.current.hasSelection()).toBe(true);
  });
});
```

### Integration Testing with Services

```typescript
// features/reconciliation/services/ReconciliationService.test.ts
import { ReconciliationService } from './ReconciliationService';
import { useReconciliationStore } from '../stores/reconciliationStore';

describe('ReconciliationService', () => {
  let service: ReconciliationService;
  let mockApiClient: jest.Mocked<ApiClient>;

  beforeEach(() => {
    mockApiClient = createMockApiClient();
    service = new ReconciliationService(mockApiClient, mockNotificationService);
    
    // Reset store
    useReconciliationStore.getState().clearSelection();
  });

  it('should update store when task is created', async () => {
    const mockTask = { id: 'task-123', name: 'Test Task' };
    mockApiClient.post.mockResolvedValue(mockTask);
    
    await service.createTask({ name: 'Test Task' });
    
    const state = useReconciliationStore.getState();
    expect(state.selectedTaskId).toBe('task-123');
  });

  it('should clear selection when selected task is deleted', async () => {
    // Setup: select a task
    useReconciliationStore.getState().setSelectedTask('task-123');
    
    await service.deleteTask('task-123');
    
    const state = useReconciliationStore.getState();
    expect(state.selectedTaskId).toBeNull();
  });
});
```

## Best Practices

### 1. Store Organization
```typescript
// ✅ Good: Small, focused stores
const useTaskFiltersStore = create(/* filters only */);
const useTaskSelectionStore = create(/* selection only */);

// ❌ Avoid: Monolithic stores
const useEverythingStore = create(/* all app state */);
```

### 2. Action Naming
```typescript
// ✅ Good: Clear, verb-based actions
setSelectedTask, toggleBulkSelection, clearFilters

// ❌ Avoid: Unclear actions  
updateState, changeValue, handleClick
```

### 3. Computed Values
```typescript
// ✅ Good: Computed values as functions
export const useReconciliationStore = create<Store>((set, get) => ({
  selectedTaskIds: [],
  selectionCount: () => get().selectedTaskIds.length,
  hasSelection: () => get().selectedTaskIds.length > 0,
}));
```

### 4. Performance Optimization
```typescript
// ✅ Good: Use selectors to prevent unnecessary re-renders
const selectedTaskId = useReconciliationStore((state) => state.selectedTaskId);

// ❌ Avoid: Selecting entire store
const store = useReconciliationStore(); // Re-renders on any state change
```

### 5. TypeScript Integration
```typescript
// ✅ Good: Strong typing
interface ReconciliationStore {
  selectedTaskId: string | null;
  setSelectedTask: (taskId: string | null) => void;
}

// ❌ Avoid: Any types
interface BadStore {
  data: any;
  updateData: (data: any) => void;
}
```

## Implementation Roadmap

### Week 1: Setup and Basic Stores
1. Install Zustand: `npm install zustand`
2. Create basic feature stores (reconciliation, auth)
3. Replace existing useState with Zustand in key components
4. Set up basic TypeScript interfaces

### Week 2: Service Integration
1. Integrate stores with service layer
2. Add store actions to service methods
3. Implement loading and error states in stores
4. Add basic testing

### Week 3: UI Polish and Middleware
1. Add devtools middleware for development
2. Implement persist middleware for user preferences
3. Add subscriptions for analytics and side effects
4. Optimize with selectors

### Week 4: Advanced Patterns
1. Create store slices for large stores
2. Add computed selectors
3. Implement store composition patterns
4. Performance profiling and optimization

## Migration from Current State

If currently using Context API or useState:

### Before (Context API)
```typescript
const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  return (
    <TaskContext.Provider value={{ selectedTaskId, setSelectedTaskId, viewMode, setViewMode }}>
      {children}
    </TaskContext.Provider>
  );
};

export const useTaskContext = () => {
  const context = useContext(TaskContext);
  if (!context) throw new Error('useTaskContext must be used within TaskProvider');
  return context;
};
```

### After (Zustand)
```typescript
interface TaskStore {
  selectedTaskId: string | null;
  viewMode: 'grid' | 'list';
  setSelectedTask: (taskId: string | null) => void;
  setViewMode: (mode: 'grid' | 'list') => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  selectedTaskId: null,
  viewMode: 'grid',
  setSelectedTask: (taskId) => set({ selectedTaskId: taskId }),
  setViewMode: (mode) => set({ viewMode: mode }),
}));

// No providers needed, just use the hook
const { selectedTaskId, setSelectedTask } = useTaskStore();
```

**Migration Benefits:**
- ✅ Remove provider wrapper components
- ✅ Eliminate context provider hierarchy
- ✅ Better TypeScript inference
- ✅ Smaller bundle size
- ✅ Better performance (no context re-renders)
- ✅ Easier testing (no provider setup needed)

This comprehensive approach ensures Zustand integrates perfectly with our TanStack + Chakra UI + Tailwind stack while supporting our modular architecture and scaling strategy.