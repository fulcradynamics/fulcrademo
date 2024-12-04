def determine_movement_status(data_point):
    speed_mps = data_point.get("speed", 0)
    speed_accuracy = data_point.get("speed_accuracy_meters", float("inf"))
    horizontal_accuracy = data_point.get("horizontal_accuracy_meters", float("inf"))

    # Check if speed measurement is reliable
    if speed_accuracy > 1.0:
        # Speed accuracy is poor, rely on other data
        pass

    # Determine movement status based on speed
    if speed_mps < 0.5:
        status = "Stationary"
    elif 0.5 <= speed_mps < 2:
        status = "Walking"
    elif 2 <= speed_mps < 6:
        status = "Running"
    else:
        status = "Driving"

    return status


# Example usage
data_point = {
    "speed": 11.208691596967533,
    "speed_accuracy_meters": 1.9252212050759534,
    "horizontal_accuracy_meters": 25.95595459467427,
    # ... other data fields
}

movement_status = determine_movement_status(data_point)
print(f"User is likely: {movement_status}")
