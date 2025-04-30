 CREATE DATABASE WeatherDB;
GO
USE WeatherDB;
GO
CREATE TABLE Weather (
    City NVARCHAR(100),
    Temperature INT,
    Weather NVARCHAR(100),
    Climate NVARCHAR(100)
);
GO
INSERT INTO Weather (City, Temperature, Weather, Climate) VALUES
('New York', 22, 'sunny', 'temperate'),
('Los Angeles', 25, 'partly cloudy', 'mediterranean'),
('Chicago', 18, 'cloudy', 'continental'),
('Houston', 30, 'thunderstorms', 'humid subtropical'),
('Phoenix', 35, 'sunny', 'desert'),
('Toronto', 20, 'partly cloudy', 'continental'),
('Warsaw', 16, 'overcast', 'temperate'),
('Bangalore', 28, 'rainy', 'tropical savanna'),
('London', 18, 'drizzle', 'temperate maritime'),
('Paris', 21, 'partly sunny', 'temperate'),
('Tokyo', 26, 'clear', 'humid subtropical'),
('Sydney', 22, 'windy', 'humid subtropical'),
('Cape Town', 19, 'partly cloudy', 'mediterranean'),
('Moscow', 15, 'cloudy', 'continental'),
('Rio de Janeiro', 29, 'scattered showers', 'tropical'),
('Beijing', 24, 'smoggy', 'continental'),
('Mumbai', 30, 'humid', 'tropical monsoon'),
('Cairo', 32, 'sunny', 'desert'),
('Buenos Aires', 23, 'clear', 'humid subtropical'),
('Johannesburg', 20, 'partly sunny', 'subtropical highland');
GO

