###### DELETE ######
curl -s -X DELETE "http://localhost:9000/tables/carData" | jq

curl -s -X DELETE "http://localhost:9000/schemas/carData" | jq

####### CREATE #######

curl -s -X POST "http://localhost:9000/schemas" -H "Content-Type: application/json" -d @carData_schema.json | jq 

curl -s -X POST -H "Content-Type: application/json" -d @pinot.config http://localhost:9000/tables | jq 