def find_flights(origin: str, destination: str, date: str) -> str:
    """Find available flights between origin and destination on a given date.
    
    Args:
        origin: The starting airport code or city (e.g., 'SFO').
        destination: The destination airport code or city (e.g., 'JFK').
        date: The date of the flight (e.g., '2026-07-13').
        
    Returns:
        A list of available flights with IDs and prices.
    """
    print(f"[Tool: find_flights] Called with origin={origin}, destination={destination}, date={date}")
    # Handle SFO to JFK
    if origin == "SFO" and destination in ["JFK", "New York"]:
        return "Available flights: Flight ID FL-102 (Price: $350, Time: 08:00 AM), Flight ID FL-205 (Price: $420, Time: 01:00 PM)"
    # Handle SFO to CDG (Paris)
    elif origin == "SFO" and destination in ["CDG", "Paris", "France"]:
        return "Available flights: Flight ID FL-901 (Price: $850, Time: 04:00 PM), Flight ID FL-902 (Price: $950, Time: 09:30 PM)"
    # Handle Cleveland SFO-CLE
    elif origin == "SFO" and destination in ["CLE", "Cleveland"]:
        return "Available flights: Flight ID FL-501 (Price: $310, Time: 10:00 AM), Flight ID FL-502 (Price: $380, Time: 03:00 PM)"
    else:
        return f"No direct flights found from {origin} to {destination} on {date}. Try SFO to CDG, SFO to CLE, or SFO to JFK."

def book_flight(flight_id: str) -> str:
    """Book a flight using its flight ID.
    
    Args:
        flight_id: The unique ID of the flight to book.
        
    Returns:
        A confirmation message with a booking reference code.
    """
    print(f"[Tool: book_flight] Called with flight_id={flight_id}")
    valid_ids = ["FL-102", "FL-205", "FL-501", "FL-502", "FL-901", "FL-902"]
    if flight_id in valid_ids:
        ref_code = (hash(flight_id) % 9000) + 1000
        return f"Successfully booked flight {flight_id}! Booking confirmation reference: BK-{ref_code}."
    else:
        return f"Failed to book flight {flight_id}. Invalid flight ID. Please pick from available flights."
