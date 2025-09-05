# Frontend Update Guide - Queue-Level Location Architecture

## 🚨 Breaking Changes

### Service Creation

**Before:** Services required `location_id`

```json
{
  "name": "Festival Makeup",
  "location_id": "location_123", // ❌ REMOVED
  "category": "makeup",
  "price": 50.0
}
```

**After:** Services are location-agnostic

```json
{
  "name": "Festival Makeup",
  "category": "makeup",
  "price": 50.0
}
```

### Queue Creation

**Before:** Queues inherited location from service

```json
{
  "name": "Makeup Queue",
  "service_id": "service_123"
}
```

**After:** Queues require `location_id` and support events

```json
{
  "name": "Amsterdam Festival Makeup",
  "service_id": "service_123",
  "location_id": "location_456", // ✅ REQUIRED
  "event_name": "Amsterdam Festival", // ✅ NEW
  "event_start_date": "2024-09-15T00:00:00Z", // ✅ NEW
  "event_end_date": "2024-09-17T23:59:59Z", // ✅ NEW
  "is_mobile_queue": true // ✅ NEW
}
```

## 📋 Updated Endpoints

### 1. Service Endpoints

| Endpoint             | Method | Change       | Notes                                     |
| -------------------- | ------ | ------------ | ----------------------------------------- |
| `POST /services/`    | POST   | **BREAKING** | Remove `location_id` from request body    |
| `GET /services/{id}` | GET    | **BREAKING** | Response no longer includes `location_id` |
| `PUT /services/{id}` | PUT    | **BREAKING** | Remove `location_id` from request body    |

### 2. Queue Endpoints

| Endpoint           | Method | Change       | Notes                                                |
| ------------------ | ------ | ------------ | ---------------------------------------------------- |
| `POST /queues/`    | POST   | **BREAKING** | Add required `location_id` + optional event fields   |
| `GET /queues/`     | GET    | **ENHANCED** | Add query params: `event_name`, `is_mobile_queue`    |
| `GET /queues/{id}` | GET    | **ENHANCED** | Response now includes `location_id` and event fields |
| `PUT /queues/{id}` | PUT    | **ENHANCED** | Support updating event fields                        |

### 3. New Queue Endpoints

| Endpoint                          | Method | Purpose                               |
| --------------------------------- | ------ | ------------------------------------- |
| `GET /queues/events/{event_name}` | GET    | Get all queues for specific event     |
| `GET /queues/mobile`              | GET    | Get all mobile/event-based queues     |
| `POST /queues/events`             | POST   | Create event queue (staff/admin only) |

### 4. Location Endpoints

| Endpoint                       | Method | Change      | Notes                                |
| ------------------------------ | ------ | ----------- | ------------------------------------ |
| `GET /locations/{id}/services` | GET    | **REMOVED** | Services no longer tied to locations |
| `GET /locations/{id}/queues`   | GET    | **NEW**     | Get all queues at location           |

## 🔄 Migration Steps

### 1. Update Service Forms

- Remove location selection from service creation
- Services are now global/organization-wide

### 2. Update Queue Forms

- Add location selection (required)
- Add event fields (optional):
  - Event name
  - Start date
  - End date
  - Mobile queue checkbox

### 3. Update Queue Lists

- Add filters for:
  - Event name
  - Mobile queues
  - Location
- Update queue cards to show location and event info

### 4. Update Navigation

- Replace "Services by Location" with "Queues by Location"
- Add "Event Queues" section

## 📊 New Data Structure

### Queue Response (Enhanced)

```json
{
  "queue_id": "queue_123",
  "name": "Amsterdam Festival Makeup",
  "description": "Makeup queue for Amsterdam Festival",
  "service_id": "service_123",
  "location_id": "location_456", // ✅ NEW
  "event_name": "Amsterdam Festival", // ✅ NEW
  "event_start_date": "2024-09-15T00:00:00Z", // ✅ NEW
  "event_end_date": "2024-09-17T23:59:59Z", // ✅ NEW
  "is_mobile_queue": true, // ✅ NEW
  "status": "active",
  "max_capacity": 50,
  "estimated_service_time": 45,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Service Response (Simplified)

```json
{
  "service_id": "service_123",
  "name": "Festival Makeup",
  "description": "Professional festival makeup",
  "category": "makeup",
  "duration_minutes": 45,
  "price": 50.0,
  "is_active": true,
  "max_daily_capacity": 100,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
  // ❌ location_id removed
}
```

## 🎯 New Query Parameters

### Queue Filtering

```
GET /queues?event_name=Amsterdam Festival
GET /queues?is_mobile_queue=true
GET /queues?location_id=location_456
GET /queues?event_start_date=2024-09-15&event_end_date=2024-09-17
```

## 🚀 Event Queue Creation

### New Endpoint: `POST /queues/events`

```json
{
  "service_id": "service_123",
  "location_id": "location_456",
  "event_name": "Amsterdam Festival",
  "event_start_date": "2024-09-15T00:00:00Z",
  "event_end_date": "2024-09-17T23:59:59Z",
  "queue_name": "Amsterdam Festival Makeup",
  "description": "Makeup queue for Amsterdam Festival",
  "max_capacity": 50,
  "estimated_service_time": 45
}
```

## ⚠️ Important Notes

1. **Backward Compatibility**: Existing queues will have `location_id` migrated from their service
2. **Event Fields**: All event fields are optional for regular queues
3. **Mobile Queues**: Use `is_mobile_queue=true` for event-based queues
4. **Location Access**: Use `GET /locations/{id}/queues` instead of services
5. **Service Management**: Services are now global - no location-specific services

## 🧪 Testing

Test the new endpoints:

- Create a service without location
- Create an event queue with location and event details
- Query mobile queues
- Query queues by event name
- Query queues by location

This architecture supports your festival makeup business perfectly! 🎨✨
