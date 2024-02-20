CREATE TABLE Users(Name, Password);
CREATE TABLE Trackers(Name, TtnIdentifier, LastSeen);
CREATE TABLE Positions(TrackerID, Timestamp, Latitude, Longitude);
CREATE TABLE UserTrackers(UserID, TrackerID);
