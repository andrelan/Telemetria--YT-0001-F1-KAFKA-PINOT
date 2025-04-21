# PinotAPI

## Create Schema

```bash
curl -X POST "http://localhost:9000/schemas" -H "Content-Type: application/json" -d @carData_schema.json
```

## Create Table

```bash
curl -X POST -H "Content-Type: application/json" -d @pinot.config http://localhost:9000/tables
```