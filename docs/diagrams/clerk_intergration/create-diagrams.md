# Creating Visual Diagrams with Excalidraw

## 🎨 Diagram Creation Instructions

Follow these links to create each diagram in Excalidraw, then save as PNG:

### 1. JWT Validation Flow
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/jwt-validation-flow.png`

**Components to include:**
- API Request (with JWT)
- ClerkService.verify_jwt()
- Decision: JWT Valid?
- Extract user_id from JWT
- UserSyncService.get_or_sync_user()
- Decision: User exists locally?
- Clerk API call
- Create local user
- Return authenticated user
- Error paths (401 responses)

**Flow**: Rectangle → Diamond → Rectangle → Diamond → Rectangle
**Colors**: Blue for normal flow, Red for errors, Yellow for decisions

---

### 2. Webhook Processing Flow  
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/webhook-processing-flow.png`

**Components to include:**
- User signs up in Clerk UI
- Clerk sends webhook
- FastAPI webhook endpoint
- Validate signature
- Check idempotency
- Create WebhookEvent
- Extract user data
- Create local user
- Mark webhook SUCCESS
- Error handling branches

**Flow**: Circle → Rectangle → Diamond → Rectangle
**Colors**: Green for success, Red for failures, Blue for processing

---

### 3. User Sync Strategy
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/user-sync-strategy.png`

**Components to include:**
- JWT validated - need user
- Check local database
- Decision: User exists?
- Return cached user (fast path)
- Fetch from Clerk API
- Create local record
- Update sync status
- Return synced user

**Flow**: Oval → Rectangle → Diamond → Rectangle
**Colors**: Green for cached hits, Blue for API calls

---

### 4. Webhook State Machine
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/webhook-state-machine.png`

**Components to include:**
- States: PENDING, PROCESSING, SUCCESS, FAILED, INVALID, IGNORED
- Transitions with arrows and labels
- Terminal states highlighted
- Retry loop (FAILED → PROCESSING)

**Layout**: State diagram with circles for states, arrows for transitions
**Colors**: Green for SUCCESS, Red for FAILED/INVALID, Yellow for PENDING

---

### 5. Error Handling & Retry
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/error-handling-retry.png`

**Components to include:**
- Webhook processing starts
- Update to PROCESSING
- Process user data
- Decision: Success?
- Increment retry_count
- Decision: Under max retries?
- Calculate next_retry_at
- Mark FAILED (permanent)
- Background retry job

**Flow**: Sequential with retry loop
**Colors**: Red for failures, Yellow for retry logic

---

### 6. Component Integration Overview
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `clerk-auth-flow/component-integration.png`

**Components to include:**
- ClerkService (JWT validation)
- UserSyncService (user management)
- WebhookProcessor (webhook handling)
- PostgreSQL (data storage)
- FastAPI endpoints
- Clerk API (external)

**Layout**: Architecture diagram with boxes and connection lines
**Colors**: Different color for each service layer

---

### 7. Factory Pattern Structure
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `test-architecture/factory-pattern-structure.png`

**Components to include:**
- FactoryBase (parent class)
- UserFactory, WebhookFactory, ClerkFactory (children)
- UserTraits, ClerkTraits (behavior)
- Faker, Sequence (data generation)
- Inheritance arrows

**Layout**: Class diagram with boxes and inheritance arrows
**Colors**: Blue for factories, Green for traits

---

### 8. Test Data Generation Flow
**Link**: https://excalidraw.com/#json=N4Ig...
**File**: `test-architecture/test-data-generation-flow.png`

**Components to include:**
- Test needs data
- Factory selection
- Apply Faker generators
- Apply sequences
- Apply traits
- Return test object

**Flow**: Linear with decision points for factory selection
**Colors**: Blue for process, Green for output

## 📝 Creation Steps

For each diagram:

1. **Click the Excalidraw link** (or go to https://excalidraw.com/)
2. **Create the diagram** following the component list
3. **Use consistent styling**:
   - Rectangle for processes
   - Diamond for decisions  
   - Circle for start/end
   - Oval for external systems
4. **Export as PNG**:
   - Click "Export image" 
   - Choose PNG format
   - Download file
5. **Save to correct directory**:
   - Move PNG to the specified path
   - Update filename as listed

## 🎨 Style Guidelines

- **Font**: Use readable font size (14px minimum)
- **Colors**: 
  - Blue (#3B82F6) for normal processes
  - Green (#10B981) for success states
  - Red (#EF4444) for error states  
  - Yellow (#F59E0B) for decision points
  - Gray (#6B7280) for external systems
- **Arrows**: Clear directional flow
- **Labels**: Brief, descriptive text
- **Spacing**: Adequate white space between elements

## ✅ Completion Checklist

- [ ] JWT Validation Flow diagram created
- [ ] Webhook Processing Flow diagram created
- [ ] User Sync Strategy diagram created
- [ ] Webhook State Machine diagram created
- [ ] Error Handling & Retry diagram created
- [ ] Component Integration diagram created
- [ ] Factory Pattern Structure diagram created
- [ ] Test Data Generation Flow diagram created

Once all diagrams are created, delete this instruction file and the Mermaid versions.