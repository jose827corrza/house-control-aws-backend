# House Control AWS Backend

## Data Structure in DynamoDB

### users table


### houses table

```json
{
  "PK": "house-unique-uuid",
  "actuators": {
    "actuator-unique-uuid": {
      "name": "Kitchen",
      "status": true
    },
    "another-unique-uuid": {
      "name": "living room",
      "status": false
    }
  }
}
```