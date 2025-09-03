# RBAC Testing Guide for Python/FastAPI

## Coming from Ruby/RSpec? Here's what you need to know:

### Test Structure Comparison

| Ruby/RSpec | Python/Pytest | Purpose |
|------------|---------------|---------|
| `spec/` | `tests/` | Test directory |
| `describe` | `class Test*` | Test grouping |
| `it` | `def test_*` | Individual test |
| `let(:var)` | `@pytest.fixture` | Test data setup |
| `before(:each)` | fixture with function scope | Setup before each test |
| `expect(x).to eq(y)` | `assert x == y` | Assertions |
| `expect { }.to raise_error` | `with pytest.raises()` | Exception testing |
| `FactoryBot.create` | fixtures or factory_boy | Test data creation |
| `DatabaseCleaner` | fixture with session rollback | Database cleanup |

### Running Tests

```bash
# Run all tests
cd backend
uv run pytest

# Run specific test file
uv run pytest tests/models/test_rbac_models.py

# Run specific test class
uv run pytest tests/models/test_rbac_models.py::TestRoleModel

# Run specific test method
uv run pytest tests/models/test_rbac_models.py::TestRoleModel::test_role_creation

# Run with verbose output (like RSpec's --format documentation)
uv run pytest -v

# Run with coverage (like SimpleCov)
uv run pytest --cov=app --cov-report=html

# Run only tests matching a pattern
uv run pytest -k "permission"

# Show print statements (like puts in Ruby)
uv run pytest -s
```

### Understanding Python Test Concepts

#### 1. **Fixtures** (like Ruby's `let` and `before`)

```python
@pytest.fixture
def sample_role(session):
    """This runs before each test that uses it"""
    role = Role(name="test", permissions=[])
    session.add(role)
    session.commit()
    return role

def test_something(sample_role):  # Fixture injected as parameter
    assert sample_role.name == "test"
```

Ruby equivalent:
```ruby
let(:sample_role) { create(:role, name: "test") }

it "tests something" do
  expect(sample_role.name).to eq("test")
end
```

#### 2. **Assertions** (like Ruby's expectations)

```python
# Python
assert user.name == "John"
assert user.age > 18
assert "admin" in user.roles
assert user.active is True

# Ruby equivalent
expect(user.name).to eq("John")
expect(user.age).to be > 18
expect(user.roles).to include("admin")
expect(user.active?).to be true
```

#### 3. **Testing Exceptions**

```python
# Python
with pytest.raises(ValueError) as exc_info:
    role.add_permission("")
assert "cannot be empty" in str(exc_info.value)

# Ruby equivalent
expect { role.add_permission("") }.to raise_error(ValueError, /cannot be empty/)
```

#### 4. **Parametrized Tests** (like Ruby's shared examples)

```python
@pytest.mark.parametrize("input,expected", [
    ("admin", True),
    ("user", False),
    ("guest", False),
])
def test_is_admin_role(input, expected):
    assert is_admin(input) == expected
```

### Test Organization

```
tests/
├── conftest.py           # Global fixtures (like spec_helper.rb)
├── factories/            # Test data factories (like FactoryBot)
├── models/              # Model tests (like spec/models/)
│   └── test_rbac_models.py
├── services/            # Service/business logic tests
│   ├── test_role_service.py
│   └── test_user_role_service.py
├── seeders/             # Seeder tests
│   └── test_rbac_seeder.py
└── integration/         # Integration tests (like feature specs)
```

### Common Testing Patterns

#### Setup and Teardown
```python
class TestSomething:
    def setup_method(self):
        """Runs before each test method (like before(:each))"""
        self.data = prepare_data()
    
    def teardown_method(self):
        """Runs after each test method (like after(:each))"""
        cleanup_data()
```

#### Mocking (like Ruby's double/stub)
```python
from unittest.mock import Mock, patch

# Create a mock
mock_service = Mock()
mock_service.get_user.return_value = User(name="Test")

# Patch a method
@patch('app.services.email_service.send')
def test_something(mock_send):
    mock_send.return_value = True
    # Your test code
```

### Tips for Ruby Developers

1. **No `!` methods**: Python doesn't have bang methods. Methods either return values or raise exceptions.

2. **Truthiness differs**: 
   - Ruby: only `nil` and `false` are falsy
   - Python: `None`, `False`, `0`, `""`, `[]`, `{}` are all falsy

3. **Use `is` for identity**:
   ```python
   assert result is None  # Not == None
   assert flag is True    # Not == True
   ```

4. **Fixtures are injected**: Unlike Ruby's `let`, fixtures are passed as function parameters.

5. **No implicit returns**: Always use explicit `assert` statements.

### Debugging Tests

```bash
# Drop into debugger on failure
uv run pytest --pdb

# Show local variables on failure
uv run pytest -l

# Stop on first failure
uv run pytest -x

# Show slowest tests
uv run pytest --durations=10
```

### What to Test Next?

As exercises, try writing tests for:

1. **UserRoleService** - Test user-role assignment logic
2. **RBACSeeder** - Test that default roles are created correctly
3. **Permission edge cases** - What happens with empty permissions, None values, etc.
4. **Integration tests** - Test the full flow of creating user, assigning role, checking permissions

Each test file has extensive comments explaining Python concepts in Ruby terms. Read through them to understand the patterns!