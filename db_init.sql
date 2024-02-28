CREATE TABLE Users(Name, Password);
CREATE TABLE Trackers(Name, TtnIdentifier, LastSeen, Voltage, RSSI);
CREATE TABLE Positions(TrackerID, Timestamp, Latitude, Longitude);
CREATE TABLE UserTrackers(UserID, TrackerID);
CREATE TABLE LutraMeta(Key, Value);