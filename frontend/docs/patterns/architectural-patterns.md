# Architectural Patterns for Modular React Applications

This document outlines key architectural patterns used in the Matchbot AI frontend, following Martin Fowler's modularization principles and modern React best practices.

## Core Patterns

### 1. Feature Module Pattern

Organize code by feature rather than by file type, creating self-contained modules that can be developed and tested independently.

```
features/
├── reconciliation/
│   ├── components/          # Feature UI components
│   ├── services/           # Business logic and API calls
│   ├── models/             # Domain models and types
│   ├── hooks/              # Feature-specific React hooks
│   ├── stores/             # Feature state management
│   └── __tests__/          # Feature tests
```

**Benefits:**
- High cohesion within features
- Low coupling between features
- Easy to add/remove features
- Clear ownership and responsibility

**Example Implementation:**

```typescript
// features/reconciliation/index.ts - Feature barrel export
export { ReconciliationDashboard } from './components/ReconciliationDashboard';
export { ReconciliationTaskCard } from './components/ReconciliationTaskCard';
export { useReconciliationTasks } from './hooks/useReconciliationTasks';
export { ReconciliationService } from './services/ReconciliationService';
export type { ReconciliationTask, ReconciliationStatus } from './models/types';

// Usage in other parts of the app
import { ReconciliationDashboard, useReconciliationTasks } from 'features/reconciliation';
```

### 2. Service Layer Pattern

Extract business logic from React components into dedicated service classes that handle API communication, data transformation, and business rules.

```typescript
// features/reconciliation/services/ReconciliationService.ts
export class ReconciliationService {
  constructor(
    private apiClient: ApiClient,
    private notificationService: NotificationService,
    private errorHandler: ErrorHandler
  ) {}

  async createTask(config: ReconciliationConfig): Promise<ReconciliationTask> {
    try {
      const response = await this.apiClient.post('/reconciliation/tasks', config);
      this.notificationService.success('Task created successfully');
      return new ReconciliationTask(response.data);
    } catch (error) {
      this.errorHandler.handle(error, 'Failed to create reconciliation task');
      throw error;
    }
  }

  async processTask(taskId: string): Promise<void> {
    const task = await this.getTask(taskId);
    
    if (!task.canProcess()) {
      throw new Error('Task cannot be processed in its current state');
    }

    await this.apiClient.post(`/reconciliation/tasks/${taskId}/process`);
  }
}
```

**Usage in Components:**

```typescript
// features/reconciliation/hooks/useReconciliationService.ts
export const useReconciliationService = () => {
  const apiClient = useApiClient();
  const notificationService = useNotificationService();
  const errorHandler = useErrorHandler();

  return useMemo(
    () => new ReconciliationService(apiClient, notificationService, errorHandler),
    [apiClient, notificationService, errorHandler]
  );
};

// In React component
const MyComponent = () => {
  const reconciliationService = useReconciliationService();
  
  const handleCreateTask = async (config: ReconciliationConfig) => {
    await reconciliationService.createTask(config);
  };

  return <TaskCreationForm onSubmit={handleCreateTask} />;
};
```

### 3. Domain Model Pattern

Create rich domain models that encapsulate business logic and provide a clear API for working with domain entities.

```typescript
// features/reconciliation/models/ReconciliationTask.ts
export class ReconciliationTask {
  constructor(private data: ReconciliationTaskData) {}

  get id(): string { return this.data.id; }
  get status(): ReconciliationStatus { return this.data.status; }
  get sourceRecords(): SourceRecord[] { return this.data.sourceRecords; }
  get targetRecords(): TargetRecord[] { return this.data.targetRecords; }
  get conflicts(): DataConflict[] { return this.data.conflicts; }

  calculateProgress(): number {
    const total = this.data.sourceRecords.length;
    if (total === 0) return 0;
    
    const processed = this.data.sourceRecords.filter(r => r.status !== 'pending').length;
    return Math.round((processed / total) * 100);
  }

  hasConflicts(): boolean {
    return this.data.conflicts.length > 0;
  }

  canProcess(): boolean {
    return this.data.status === 'pending' && !this.hasConflicts();
  }

  canResolveConflicts(): boolean {
    return this.hasConflicts() && this.data.status !== 'processing';
  }

  getConflictsByType(): Record<ConflictType, DataConflict[]> {
    return this.data.conflicts.reduce((acc, conflict) => {
      if (!acc[conflict.type]) acc[conflict.type] = [];
      acc[conflict.type].push(conflict);
      return acc;
    }, {} as Record<ConflictType, DataConflict[]>);
  }

  estimateCompletionTime(): Date | null {
    if (this.data.status !== 'processing') return null;
    
    const processed = this.data.sourceRecords.filter(r => r.status !== 'pending').length;
    const remaining = this.data.sourceRecords.length - processed;
    const avgProcessingTime = this.calculateAverageProcessingTime();
    
    return new Date(Date.now() + (remaining * avgProcessingTime * 1000));
  }

  private calculateAverageProcessingTime(): number {
    // Calculate average processing time based on processed records
    // Returns time in seconds
    return 2.5; // placeholder
  }
}
```

### 4. Custom Hook Pattern

Extract stateful logic and side effects into custom hooks that can be reused across components.

```typescript
// features/reconciliation/hooks/useReconciliationTasks.ts
interface UseReconciliationTasksOptions {
  filters?: TaskFilters;
  pollingInterval?: number;
  autoRefresh?: boolean;
}

export const useReconciliationTasks = (options: UseReconciliationTasksOptions = {}) => {
  const { filters, pollingInterval = 30000, autoRefresh = true } = options;
  const reconciliationService = useReconciliationService();
  
  const [state, setState] = useState<{
    tasks: ReconciliationTask[];
    loading: boolean;
    error: string | null;
    lastRefresh: Date | null;
  }>({
    tasks: [],
    loading: false,
    error: null,
    lastRefresh: null,
  });

  const fetchTasks = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const tasks = await reconciliationService.fetchTasks(filters);
      setState(prev => ({
        ...prev,
        tasks,
        loading: false,
        lastRefresh: new Date(),
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Failed to fetch tasks',
      }));
    }
  }, [reconciliationService, filters]);

  // Auto-refresh with polling
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchTasks, pollingInterval);
    return () => clearInterval(interval);
  }, [fetchTasks, pollingInterval, autoRefresh]);

  // Initial load
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const actions = useMemo(() => ({
    refresh: fetchTasks,
    createTask: async (config: ReconciliationConfig) => {
      const newTask = await reconciliationService.createTask(config);
      setState(prev => ({
        ...prev,
        tasks: [newTask, ...prev.tasks],
      }));
      return newTask;
    },
    updateTask: (taskId: string, updates: Partial<ReconciliationTaskData>) => {
      setState(prev => ({
        ...prev,
        tasks: prev.tasks.map(task => 
          task.id === taskId 
            ? new ReconciliationTask({ ...task.data, ...updates })
            : task
        ),
      }));
    },
    deleteTask: async (taskId: string) => {
      await reconciliationService.deleteTask(taskId);
      setState(prev => ({
        ...prev,
        tasks: prev.tasks.filter(task => task.id !== taskId),
      }));
    },
  }), [reconciliationService]);

  return {
    ...state,
    ...actions,
  };
};
```

### 5. Compound Component Pattern

Create flexible, composable components that work together to provide complex functionality.

```typescript
// components/shared/DataTable/DataTable.tsx
interface DataTableContextValue {
  data: any[];
  loading: boolean;
  selection: any[];
  onSelect: (item: any) => void;
  onSelectAll: () => void;
}

const DataTableContext = createContext<DataTableContextValue | null>(null);

const useDataTableContext = () => {
  const context = useContext(DataTableContext);
  if (!context) {
    throw new Error('DataTable components must be used within DataTable');
  }
  return context;
};

// Main compound component
export const DataTable = ({ children, data, loading, onSelectionChange }) => {
  const [selection, setSelection] = useState([]);

  const handleSelect = (item) => {
    setSelection(prev => 
      prev.includes(item) 
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  const handleSelectAll = () => {
    setSelection(prev => prev.length === data.length ? [] : [...data]);
  };

  useEffect(() => {
    onSelectionChange?.(selection);
  }, [selection, onSelectionChange]);

  const contextValue = {
    data,
    loading,
    selection,
    onSelect: handleSelect,
    onSelectAll: handleSelectAll,
  };

  return (
    <DataTableContext.Provider value={contextValue}>
      <Box>{children}</Box>
    </DataTableContext.Provider>
  );
};

// Sub-components
DataTable.Header = ({ children }) => {
  return <Thead>{children}</Thead>;
};

DataTable.HeaderRow = ({ children }) => {
  return <Tr>{children}</Tr>;
};

DataTable.HeaderCell = ({ children, sortable, onSort }) => {
  const [sortDirection, setSortDirection] = useState(null);

  return (
    <Th 
      cursor={sortable ? 'pointer' : 'default'}
      onClick={sortable ? () => {
        const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        setSortDirection(newDirection);
        onSort?.(newDirection);
      } : undefined}
    >
      <HStack>
        {children}
        {sortable && (
          <Icon as={sortDirection === 'asc' ? ChevronUpIcon : ChevronDownIcon} />
        )}
      </HStack>
    </Th>
  );
};

DataTable.Body = ({ children }) => {
  const { loading, data } = useDataTableContext();

  if (loading) {
    return (
      <Tbody>
        {Array(5).fill(0).map((_, i) => (
          <Tr key={i}>
            <Td colSpan={100}>
              <Skeleton height="20px" />
            </Td>
          </Tr>
        ))}
      </Tbody>
    );
  }

  return <Tbody>{children}</Tbody>;
};

DataTable.Row = ({ item, children }) => {
  const { selection, onSelect } = useDataTableContext();
  const isSelected = selection.includes(item);

  return (
    <Tr 
      bg={isSelected ? 'blue.50' : 'transparent'}
      onClick={() => onSelect(item)}
      cursor="pointer"
      _hover={{ bg: 'gray.50' }}
    >
      {children}
    </Tr>
  );
};

DataTable.Cell = ({ children }) => {
  return <Td>{children}</Td>;
};

// Usage
const TasksTable = () => {
  const { tasks, loading } = useReconciliationTasks();

  return (
    <DataTable data={tasks} loading={loading}>
      <DataTable.Header>
        <DataTable.HeaderRow>
          <DataTable.HeaderCell sortable onSort={(dir) => console.log('Sort:', dir)}>
            Task ID
          </DataTable.HeaderCell>
          <DataTable.HeaderCell>Status</DataTable.HeaderCell>
          <DataTable.HeaderCell>Progress</DataTable.HeaderCell>
        </DataTable.HeaderRow>
      </DataTable.Header>
      <DataTable.Body>
        {tasks.map(task => (
          <DataTable.Row key={task.id} item={task}>
            <DataTable.Cell>{task.id}</DataTable.Cell>
            <DataTable.Cell><StatusBadge status={task.status} /></DataTable.Cell>
            <DataTable.Cell>{task.calculateProgress()}%</DataTable.Cell>
          </DataTable.Row>
        ))}
      </DataTable.Body>
    </DataTable>
  );
};
```

### 6. Error Boundary Pattern

Implement error boundaries to gracefully handle errors at different levels of the application.

```typescript
// shared/components/ErrorBoundary/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to monitoring service
    this.props.onError?.(error, errorInfo);
    
    // Report to error tracking service
    if (this.props.reportError) {
      reportError(error, {
        errorId: this.state.errorId,
        componentStack: errorInfo.componentStack,
        feature: this.props.feature,
      });
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.state.errorId);
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorId={this.state.errorId}
          onReset={() => this.setState({ hasError: false, error: null, errorId: null })}
          feature={this.props.feature}
        />
      );
    }

    return this.props.children;
  }
}

// Feature-level error boundary
export const FeatureErrorBoundary: React.FC<{
  feature: string;
  children: React.ReactNode;
}> = ({ feature, children }) => {
  return (
    <ErrorBoundary
      feature={feature}
      reportError={true}
      fallback={(error, errorId) => (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <VStack align="start" spacing={2}>
            <Text fontWeight="medium">
              Something went wrong in {feature}
            </Text>
            <Text fontSize="sm" color="gray.600">
              Error ID: {errorId}
            </Text>
            <Button 
              size="sm" 
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </VStack>
        </Alert>
      )}
    >
      {children}
    </ErrorBoundary>
  );
};

// Usage
const App = () => {
  return (
    <Router>
      <Routes>
        <Route 
          path="/reconciliation/*" 
          element={
            <FeatureErrorBoundary feature="reconciliation">
              <ReconciliationFeature />
            </FeatureErrorBoundary>
          } 
        />
      </Routes>
    </Router>
  );
};
```

### 7. Provider Pattern

Use React Context and providers to share state and services across component trees.

```typescript
// features/reconciliation/providers/ReconciliationProvider.tsx
interface ReconciliationContextValue {
  service: ReconciliationService;
  settings: ReconciliationSettings;
  updateSettings: (updates: Partial<ReconciliationSettings>) => void;
}

const ReconciliationContext = createContext<ReconciliationContextValue | null>(null);

export const useReconciliation = () => {
  const context = useContext(ReconciliationContext);
  if (!context) {
    throw new Error('useReconciliation must be used within ReconciliationProvider');
  }
  return context;
};

export const ReconciliationProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [settings, setSettings] = useState<ReconciliationSettings>(() => 
    loadSettingsFromStorage()
  );

  const service = useMemo(() => {
    return new ReconciliationService(/* dependencies */);
  }, []);

  const updateSettings = useCallback((updates: Partial<ReconciliationSettings>) => {
    setSettings(prev => {
      const newSettings = { ...prev, ...updates };
      saveSettingsToStorage(newSettings);
      return newSettings;
    });
  }, []);

  const contextValue = useMemo(() => ({
    service,
    settings,
    updateSettings,
  }), [service, settings, updateSettings]);

  return (
    <ReconciliationContext.Provider value={contextValue}>
      {children}
    </ReconciliationContext.Provider>
  );
};
```

### 8. Repository Pattern

Abstract data access logic to provide a consistent interface for different data sources.

```typescript
// shared/repositories/Repository.ts
export interface Repository<T, ID = string> {
  findById(id: ID): Promise<T | null>;
  findAll(filter?: any): Promise<T[]>;
  create(data: Omit<T, 'id'>): Promise<T>;
  update(id: ID, data: Partial<T>): Promise<T>;
  delete(id: ID): Promise<void>;
}

// features/reconciliation/repositories/ReconciliationTaskRepository.ts
export class ReconciliationTaskRepository implements Repository<ReconciliationTask> {
  constructor(
    private apiClient: ApiClient,
    private cacheService: CacheService
  ) {}

  async findById(id: string): Promise<ReconciliationTask | null> {
    // Check cache first
    const cached = this.cacheService.get(`task:${id}`);
    if (cached) return new ReconciliationTask(cached);

    const response = await this.apiClient.get(`/reconciliation/tasks/${id}`);
    if (!response.data) return null;

    // Cache the result
    this.cacheService.set(`task:${id}`, response.data, 300000); // 5 minutes

    return new ReconciliationTask(response.data);
  }

  async findAll(filter?: TaskFilters): Promise<ReconciliationTask[]> {
    const cacheKey = `tasks:${JSON.stringify(filter)}`;
    const cached = this.cacheService.get(cacheKey);
    if (cached) return cached.map(data => new ReconciliationTask(data));

    const response = await this.apiClient.get('/reconciliation/tasks', { params: filter });
    const tasks = response.data.map(data => new ReconciliationTask(data));

    // Cache for 1 minute
    this.cacheService.set(cacheKey, response.data, 60000);

    return tasks;
  }

  async create(data: CreateReconciliationTaskData): Promise<ReconciliationTask> {
    const response = await this.apiClient.post('/reconciliation/tasks', data);
    const task = new ReconciliationTask(response.data);

    // Invalidate list caches
    this.cacheService.clearPattern('tasks:*');

    return task;
  }

  async update(id: string, data: UpdateReconciliationTaskData): Promise<ReconciliationTask> {
    const response = await this.apiClient.patch(`/reconciliation/tasks/${id}`, data);
    const task = new ReconciliationTask(response.data);

    // Update cache
    this.cacheService.set(`task:${id}`, response.data, 300000);
    this.cacheService.clearPattern('tasks:*');

    return task;
  }

  async delete(id: string): Promise<void> {
    await this.apiClient.delete(`/reconciliation/tasks/${id}`);

    // Clear caches
    this.cacheService.delete(`task:${id}`);
    this.cacheService.clearPattern('tasks:*');
  }
}
```

## Pattern Integration Examples

### Complete Feature Implementation

Here's how these patterns work together in a complete feature implementation:

```typescript
// features/reconciliation/ReconciliationFeature.tsx
const ReconciliationFeature = () => {
  return (
    <FeatureErrorBoundary feature="reconciliation">
      <ReconciliationProvider>
        <Routes>
          <Route path="/" element={<ReconciliationDashboard />} />
          <Route path="/tasks/:id" element={<TaskDetails />} />
          <Route path="/create" element={<CreateTask />} />
        </Routes>
      </ReconciliationProvider>
    </FeatureErrorBoundary>
  );
};

// features/reconciliation/components/ReconciliationDashboard.tsx
const ReconciliationDashboard = () => {
  const { settings } = useReconciliation();
  const { tasks, loading, createTask, updateTask } = useReconciliationTasks({
    filters: settings.defaultFilters,
    autoRefresh: settings.autoRefresh,
  });

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">Reconciliation Dashboard</Heading>
        <Button onClick={() => /* navigate to create */}>
          Create New Task
        </Button>
      </HStack>

      <DataTable data={tasks} loading={loading}>
        <DataTable.Header>
          <DataTable.HeaderRow>
            <DataTable.HeaderCell sortable>Task ID</DataTable.HeaderCell>
            <DataTable.HeaderCell>Status</DataTable.HeaderCell>
            <DataTable.HeaderCell>Progress</DataTable.HeaderCell>
            <DataTable.HeaderCell>Actions</DataTable.HeaderCell>
          </DataTable.HeaderRow>
        </DataTable.Header>
        <DataTable.Body>
          {tasks.map(task => (
            <DataTable.Row key={task.id} item={task}>
              <DataTable.Cell>{task.id}</DataTable.Cell>
              <DataTable.Cell>
                <StatusBadge status={task.status} />
              </DataTable.Cell>
              <DataTable.Cell>
                <Progress value={task.calculateProgress()} />
              </DataTable.Cell>
              <DataTable.Cell>
                <TaskActions 
                  task={task} 
                  onUpdate={(updates) => updateTask(task.id, updates)}
                />
              </DataTable.Cell>
            </DataTable.Row>
          ))}
        </DataTable.Body>
      </DataTable>
    </VStack>
  );
};
```

These patterns provide a robust foundation for building scalable, maintainable React applications that can grow from MVP to enterprise scale while maintaining code quality and developer productivity.