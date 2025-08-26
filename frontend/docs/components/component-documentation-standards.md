# Component Documentation Standards

This document outlines the documentation standards for React components in the Matchbot AI frontend, following our modular architecture principles.

## Component Documentation Template

Each component should include comprehensive documentation covering usage, props, examples, and design considerations.

### Standard Documentation Structure

```markdown
# ComponentName

Brief description of what the component does and when to use it.

## Usage

```typescript
import { ComponentName } from 'features/[feature]/components';

const Example = () => (
  <ComponentName
    prop1="value"
    prop2={42}
    onAction={handleAction}
  />
);
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| prop1 | string | Yes | - | Description of prop1 |
| prop2 | number | No | 0 | Description of prop2 |
| onAction | function | No | - | Callback when action occurs |

## Examples

### Basic Usage
[Code example with explanation]

### Advanced Usage  
[Code example with explanation]

## Design Considerations

- Accessibility features
- Responsive behavior
- Performance considerations
- Testing notes

## Related Components

- Links to related components
- When to use alternatives
```

## Shared Component Examples

### DataTable Component

```typescript
// src/components/shared/DataTable/DataTable.tsx
interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
  sorting?: {
    column: keyof T;
    direction: 'asc' | 'desc';
    onSort: (column: keyof T, direction: 'asc' | 'desc') => void;
  };
  filters?: Record<keyof T, string>;
  onFilterChange?: (filters: Record<keyof T, string>) => void;
  selection?: {
    selectedRows: T[];
    onSelectionChange: (rows: T[]) => void;
    selectable: (row: T) => boolean;
  };
  actions?: Array<{
    label: string;
    icon?: React.ReactNode;
    onClick: (row: T) => void;
    disabled?: (row: T) => boolean;
    variant?: 'primary' | 'secondary' | 'danger';
  }>;
  emptyState?: React.ReactNode;
  errorState?: React.ReactNode;
}

export const DataTable = <T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  pagination,
  sorting,
  filters,
  onFilterChange,
  selection,
  actions,
  emptyState,
  errorState,
}: DataTableProps<T>) => {
  // Implementation with Chakra UI Table components
  return (
    <Box>
      {/* Filters */}
      {onFilterChange && (
        <HStack spacing={4} mb={4}>
          {columns
            .filter(col => col.filterable)
            .map(col => (
              <FormControl key={String(col.key)} maxW="200px">
                <FormLabel>{col.header}</FormLabel>
                <Input
                  value={filters?.[col.key] || ''}
                  onChange={(e) => onFilterChange({
                    ...filters,
                    [col.key]: e.target.value
                  })}
                  placeholder={`Filter ${col.header}`}
                />
              </FormControl>
            ))
          }
        </HStack>
      )}

      {/* Table */}
      <TableContainer>
        <Table variant="simple">
          <Thead>
            <Tr>
              {selection && <Th width="50px" />}
              {columns.map((column) => (
                <Th 
                  key={String(column.key)} 
                  width={column.width}
                  cursor={column.sortable ? 'pointer' : 'default'}
                  onClick={column.sortable && sorting ? 
                    () => sorting.onSort(
                      column.key, 
                      sorting.column === column.key && sorting.direction === 'asc' 
                        ? 'desc' 
                        : 'asc'
                    ) : undefined
                  }
                >
                  <HStack>
                    <Text>{column.header}</Text>
                    {column.sortable && sorting?.column === column.key && (
                      <Icon as={sorting.direction === 'asc' ? ChevronUpIcon : ChevronDownIcon} />
                    )}
                  </HStack>
                </Th>
              ))}
              {actions && <Th width="120px">Actions</Th>}
            </Tr>
          </Thead>
          <Tbody>
            {loading ? (
              Array(5).fill(0).map((_, index) => (
                <Tr key={index}>
                  {selection && <Td><Skeleton height="20px" /></Td>}
                  {columns.map((column) => (
                    <Td key={String(column.key)}>
                      <Skeleton height="20px" />
                    </Td>
                  ))}
                  {actions && <Td><Skeleton height="20px" /></Td>}
                </Tr>
              ))
            ) : data.length === 0 ? (
              <Tr>
                <Td colSpan={columns.length + (selection ? 1 : 0) + (actions ? 1 : 0)}>
                  {emptyState || (
                    <VStack py={8} spacing={4}>
                      <Icon as={SearchIcon} w={8} h={8} color="gray.400" />
                      <Text color="gray.500">No data found</Text>
                    </VStack>
                  )}
                </Td>
              </Tr>
            ) : (
              data.map((row, index) => (
                <Tr key={index}>
                  {selection && (
                    <Td>
                      <Checkbox
                        isChecked={selection.selectedRows.includes(row)}
                        isDisabled={!selection.selectable(row)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            selection.onSelectionChange([...selection.selectedRows, row]);
                          } else {
                            selection.onSelectionChange(
                              selection.selectedRows.filter(r => r !== row)
                            );
                          }
                        }}
                      />
                    </Td>
                  )}
                  {columns.map((column) => (
                    <Td key={String(column.key)}>
                      {column.render 
                        ? column.render(row[column.key], row)
                        : String(row[column.key])
                      }
                    </Td>
                  ))}
                  {actions && (
                    <Td>
                      <Menu>
                        <MenuButton as={IconButton} icon={<MoreVertical />} variant="ghost" size="sm" />
                        <MenuList>
                          {actions.map((action) => (
                            <MenuItem
                              key={action.label}
                              icon={action.icon}
                              onClick={() => action.onClick(row)}
                              isDisabled={action.disabled?.(row)}
                              color={action.variant === 'danger' ? 'red.500' : undefined}
                            >
                              {action.label}
                            </MenuItem>
                          ))}
                        </MenuList>
                      </Menu>
                    </Td>
                  )}
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {pagination && (
        <HStack justify="space-between" mt={4}>
          <Text fontSize="sm" color="gray.600">
            Showing {Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.total)} to{' '}
            {Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total} results
          </Text>
          <ButtonGroup size="sm" variant="outline">
            <IconButton
              aria-label="Previous page"
              icon={<ChevronLeftIcon />}
              isDisabled={pagination.page === 1}
              onClick={() => pagination.onPageChange(pagination.page - 1)}
            />
            <Button isDisabled>{pagination.page}</Button>
            <IconButton
              aria-label="Next page"
              icon={<ChevronRightIcon />}
              isDisabled={pagination.page * pagination.pageSize >= pagination.total}
              onClick={() => pagination.onPageChange(pagination.page + 1)}
            />
          </ButtonGroup>
        </HStack>
      )}
    </Box>
  );
};
```

### StatusBadge Component

```typescript
// src/components/shared/StatusBadge/StatusBadge.tsx
type StatusVariant = 'success' | 'warning' | 'error' | 'info' | 'neutral';

interface StatusConfig {
  label: string;
  colorScheme: string;
  icon?: React.ReactNode;
}

interface StatusBadgeProps {
  status: string;
  variant?: StatusVariant;
  customConfig?: Record<string, StatusConfig>;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

const defaultStatusConfigs: Record<StatusVariant, Record<string, StatusConfig>> = {
  success: {
    completed: { label: 'Completed', colorScheme: 'green', icon: <CheckIcon /> },
    active: { label: 'Active', colorScheme: 'green' },
    approved: { label: 'Approved', colorScheme: 'green' },
  },
  warning: {
    pending: { label: 'Pending', colorScheme: 'yellow', icon: <TimeIcon /> },
    processing: { label: 'Processing', colorScheme: 'yellow' },
    review: { label: 'Under Review', colorScheme: 'yellow' },
  },
  error: {
    failed: { label: 'Failed', colorScheme: 'red', icon: <WarningIcon /> },
    error: { label: 'Error', colorScheme: 'red' },
    rejected: { label: 'Rejected', colorScheme: 'red' },
  },
  info: {
    draft: { label: 'Draft', colorScheme: 'blue' },
    scheduled: { label: 'Scheduled', colorScheme: 'blue' },
    new: { label: 'New', colorScheme: 'blue' },
  },
  neutral: {
    inactive: { label: 'Inactive', colorScheme: 'gray' },
    disabled: { label: 'Disabled', colorScheme: 'gray' },
    cancelled: { label: 'Cancelled', colorScheme: 'gray' },
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'neutral',
  customConfig,
  size = 'md',
  showIcon = true,
}) => {
  const configs = customConfig || defaultStatusConfigs[variant];
  const config = configs[status.toLowerCase()] || {
    label: status,
    colorScheme: 'gray',
  };

  return (
    <Badge
      colorScheme={config.colorScheme}
      variant="subtle"
      fontSize={size === 'sm' ? 'xs' : size === 'lg' ? 'md' : 'sm'}
      px={size === 'sm' ? 2 : size === 'lg' ? 4 : 3}
      py={size === 'sm' ? 1 : 2}
      borderRadius="full"
      display="flex"
      alignItems="center"
      gap={showIcon && config.icon ? 1 : 0}
    >
      {showIcon && config.icon && (
        <Box as="span" fontSize={size === 'sm' ? 'xs' : 'sm'}>
          {config.icon}
        </Box>
      )}
      {config.label}
    </Badge>
  );
};
```

## Feature Component Examples

### ReconciliationTaskCard

```typescript
// features/reconciliation/components/ReconciliationTaskCard/ReconciliationTaskCard.tsx
interface ReconciliationTaskCardProps {
  task: ReconciliationTask;
  onStart: (taskId: string) => void;
  onPause: (taskId: string) => void;
  onViewDetails: (taskId: string) => void;
  onResolveConflicts: (taskId: string) => void;
  onDelete: (taskId: string) => void;
  isSelected?: boolean;
  onSelect?: (taskId: string) => void;
}

export const ReconciliationTaskCard: React.FC<ReconciliationTaskCardProps> = ({
  task,
  onStart,
  onPause,
  onViewDetails,
  onResolveConflicts,
  onDelete,
  isSelected = false,
  onSelect,
}) => {
  const taskModel = new ReconciliationTaskModel(task);
  const toast = useToast();

  const handleAction = async (action: () => Promise<void>, successMessage: string) => {
    try {
      await action();
      toast({
        title: successMessage,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Action failed',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Card
      variant={isSelected ? 'elevated' : 'outline'}
      borderColor={isSelected ? 'blue.200' : undefined}
      borderWidth={isSelected ? 2 : 1}
      cursor={onSelect ? 'pointer' : 'default'}
      onClick={onSelect ? () => onSelect(task.id) : undefined}
      transition="all 0.2s"
      _hover={{
        shadow: 'md',
        borderColor: 'blue.100',
      }}
    >
      <CardBody>
        <VStack align="stretch" spacing={4}>
          {/* Header */}
          <HStack justify="space-between" align="start">
            <VStack align="start" spacing={1} flex={1}>
              <Text fontSize="lg" fontWeight="medium" color="gray.900">
                {task.name || `Task ${task.id}`}
              </Text>
              <Text fontSize="sm" color="gray.600">
                Created {formatRelativeTime(task.createdAt)}
              </Text>
            </VStack>
            <VStack align="end" spacing={2}>
              <StatusBadge status={task.status} variant="info" />
              {onSelect && (
                <Checkbox
                  isChecked={isSelected}
                  onChange={(e) => e.stopPropagation()}
                  size="lg"
                />
              )}
            </VStack>
          </HStack>

          {/* Progress */}
          <Box>
            <HStack justify="space-between" mb={2}>
              <Text fontSize="sm" fontWeight="medium">Progress</Text>
              <Text fontSize="sm" color="gray.600">
                {Math.round(taskModel.calculateProgress())}%
              </Text>
            </HStack>
            <Progress
              value={taskModel.calculateProgress()}
              colorScheme={taskModel.hasConflicts() ? 'orange' : 'blue'}
              size="sm"
              borderRadius="full"
            />
            <HStack justify="space-between" mt={1}>
              <Text fontSize="xs" color="gray.500">
                {task.processedRecords} of {task.totalRecords} processed
              </Text>
              <Text fontSize="xs" color="gray.500">
                {task.conflicts.length} conflicts
              </Text>
            </HStack>
          </Box>

          {/* Conflicts Alert */}
          {taskModel.hasConflicts() && (
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              <VStack align="start" spacing={1} flex={1}>
                <Text fontSize="sm" fontWeight="medium">
                  {task.conflicts.length} conflict{task.conflicts.length !== 1 ? 's' : ''} detected
                </Text>
                <Text fontSize="xs" color="orange.700">
                  {task.conflicts.slice(0, 2).map(c => c.field).join(', ')}
                  {task.conflicts.length > 2 && ` and ${task.conflicts.length - 2} more`}
                </Text>
              </VStack>
            </Alert>
          )}

          {/* Metrics */}
          <SimpleGrid columns={3} spacing={4}>
            <VStack spacing={1}>
              <Text fontSize="sm" fontWeight="medium" color="gray.900">
                {task.sourceRecords}
              </Text>
              <Text fontSize="xs" color="gray.500">Source Records</Text>
            </VStack>
            <VStack spacing={1}>
              <Text fontSize="sm" fontWeight="medium" color="gray.900">
                {task.targetRecords}
              </Text>
              <Text fontSize="xs" color="gray.500">Target Records</Text>
            </VStack>
            <VStack spacing={1}>
              <Text fontSize="sm" fontWeight="medium" color="gray.900">
                {task.matchedRecords}
              </Text>
              <Text fontSize="xs" color="gray.500">Matched</Text>
            </VStack>
          </SimpleGrid>

          {/* Actions */}
          <HStack spacing={2} pt={2}>
            {task.status === 'pending' && taskModel.canProcess() && (
              <Button
                size="sm"
                colorScheme="blue"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAction(() => onStart(task.id), 'Reconciliation started');
                }}
              >
                Start
              </Button>
            )}
            
            {task.status === 'processing' && (
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAction(() => onPause(task.id), 'Reconciliation paused');
                }}
              >
                Pause
              </Button>
            )}

            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                onViewDetails(task.id);
              }}
            >
              View Details
            </Button>

            {taskModel.hasConflicts() && (
              <Button
                size="sm"
                variant="outline"
                colorScheme="orange"
                onClick={(e) => {
                  e.stopPropagation();
                  onResolveConflicts(task.id);
                }}
              >
                Resolve Conflicts
              </Button>
            )}

            <Menu>
              <MenuButton
                as={IconButton}
                icon={<MoreVertical size={16} />}
                variant="ghost"
                size="sm"
                onClick={(e) => e.stopPropagation()}
              />
              <MenuList>
                <MenuItem
                  icon={<Eye size={16} />}
                  onClick={() => onViewDetails(task.id)}
                >
                  View Details
                </MenuItem>
                <MenuItem
                  icon={<Copy size={16} />}
                  onClick={() => {
                    navigator.clipboard.writeText(task.id);
                    toast({
                      title: 'Task ID copied',
                      status: 'success',
                      duration: 2000,
                    });
                  }}
                >
                  Copy ID
                </MenuItem>
                <MenuDivider />
                <MenuItem
                  icon={<Trash2 size={16} />}
                  color="red.500"
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this task?')) {
                      onDelete(task.id);
                    }
                  }}
                >
                  Delete
                </MenuItem>
              </MenuList>
            </Menu>
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  );
};
```

## Component Testing Standards

### Unit Tests Example

```typescript
// features/reconciliation/components/ReconciliationTaskCard/ReconciliationTaskCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { ReconciliationTaskCard } from './ReconciliationTaskCard';
import { mockReconciliationTask } from '../../__mocks__/reconciliationTask';

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <ChakraProvider>
      {ui}
    </ChakraProvider>
  );
};

describe('ReconciliationTaskCard', () => {
  const mockProps = {
    task: mockReconciliationTask,
    onStart: jest.fn(),
    onPause: jest.fn(),
    onViewDetails: jest.fn(),
    onResolveConflicts: jest.fn(),
    onDelete: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders task information correctly', () => {
    renderWithProviders(<ReconciliationTaskCard {...mockProps} />);
    
    expect(screen.getByText(`Task ${mockProps.task.id}`)).toBeInTheDocument();
    expect(screen.getByText(/Created/)).toBeInTheDocument();
    expect(screen.getByText('Progress')).toBeInTheDocument();
  });

  it('shows start button for pending tasks', () => {
    const pendingTask = { ...mockProps.task, status: 'pending' };
    renderWithProviders(
      <ReconciliationTaskCard {...mockProps} task={pendingTask} />
    );
    
    expect(screen.getByText('Start')).toBeInTheDocument();
  });

  it('calls onStart when start button is clicked', async () => {
    const pendingTask = { ...mockProps.task, status: 'pending' };
    renderWithProviders(
      <ReconciliationTaskCard {...mockProps} task={pendingTask} />
    );
    
    fireEvent.click(screen.getByText('Start'));
    
    await waitFor(() => {
      expect(mockProps.onStart).toHaveBeenCalledWith(pendingTask.id);
    });
  });

  it('displays conflicts when present', () => {
    const taskWithConflicts = {
      ...mockProps.task,
      conflicts: [
        { field: 'email', type: 'duplicate' },
        { field: 'name', type: 'mismatch' },
      ],
    };
    renderWithProviders(
      <ReconciliationTaskCard {...mockProps} task={taskWithConflicts} />
    );
    
    expect(screen.getByText(/2 conflicts detected/)).toBeInTheDocument();
    expect(screen.getByText('Resolve Conflicts')).toBeInTheDocument();
  });

  it('handles selection state correctly', () => {
    const onSelect = jest.fn();
    renderWithProviders(
      <ReconciliationTaskCard 
        {...mockProps} 
        isSelected={true} 
        onSelect={onSelect}
      />
    );
    
    const card = screen.getByRole('generic', { name: /task card/i });
    fireEvent.click(card);
    
    expect(onSelect).toHaveBeenCalledWith(mockProps.task.id);
  });
});
```

This documentation provides a comprehensive foundation for building and documenting React components that follow our modular architecture principles while maintaining high quality and consistency across the application.