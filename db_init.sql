CREATE TABLE Users(Name, Password);
CREATE TABLE Trackers(Name, TtnIdentifier, LastSeen, Voltage, RSSI, MinVoltage, MaxVoltage, MinRSSI, MaxRSSI);
CREATE TABLE Positions(TrackerID, Timestamp, Latitude, Longitude, Source, HDOP, Contacts);
CREATE TABLE UserTrackers(UserID, TrackerID);
CREATE TABLE LutraMeta(Key, Value);