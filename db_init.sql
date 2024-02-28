CREATE TABLE Users(Name, Password);
CREATE TABLE Trackers(Name, TtnIdentifier, LastSeen, Voltage, RSSI);
CREATE TABLE Positions(TrackerID, Timestamp, Latitude, Longitude, Source);
CREATE TABLE UserTrackers(UserID, TrackerID);
CREATE TABLE LutraMeta(Key, Value);