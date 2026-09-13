# House Control AWS Backend

## Data Structure in DynamoDB

### houses table (house-control-houses)

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

## Request and Reponses

### Fetch Houses

