migrations = {
    0: ["ALTER TABLE Trackers ADD COLUMN Voltage",
        "CREATE TABLE LutraMeta(Key, Value)"],
    1: ["ALTER TABLE Trackers ADD COLUMN RSSI"],
    2: ["ALTER TABLE Positions ADD COLUMN Source",
        "UPDATE Positions SET Source='GPS'"],
    3: ["ALTER TABLE Trackers ADD COLUMN MinVoltage",
        "ALTER TABLE Trackers ADD COLUMN MaxVoltage",
        "ALTER TABLE Trackers ADD COLUMN MinRSSI",
        "ALTER TABLE Trackers ADD COLUMN MaxRSSI"]
}
