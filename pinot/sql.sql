SELECT DriverNo, SessionKey, drs, n_gear, Utc, 'timestamp', rpm, speed, throttle, brake 
  FROM carData 
 ORDER BY DriverNo DESC 
 LIMIT 20

 ------

 SELECT *
  FROM carData 
 where DriverNo=44
 order by tsMillis desc
 LIMIT 2000
option(skipUpsert=true)
