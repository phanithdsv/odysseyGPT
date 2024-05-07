import openai
import os
import requests
import json

client = openai.OpenAI(
    # This is the default and can be omitted
    api_key=""
)



def get_user_location():
    """ Simulate asking user for location access and getting latitude and longitude. """
    print("Can we access your location? (yes/no)")
    if input().strip().lower() == 'yes':
        print("Please enter your latitude:")
        lat = float(input().strip())
        print("Please enter your longitude:")
        lon = float(input().strip())
        return lat, lon
    else:
        print("Location access denied.")
        return None, None



def get_stop_departure(global_stop_id,api_key):
    # Extract query parameters from the incoming request
    URL = 'https://external.transitapp.com/v3/public/stop_departures'


    headers = {'apiKey': api_key}

    # Parameters for the request
    params = {
        'global_stop_id': global_stop_id,
    }

    # Call the transit API and capture the response
    response = requests.get(URL, headers=headers, params=params)
    
    # Log the status code and response for debugging
    #logging.debug(f"Status Code: {response.status_code}")
    #logging.debug(f"Response: {response.json()}")

    # Filter and format the response
    route_departures = response.json().get('route_departures', [])
    formatted_stops = []
    
    for route_departure in route_departures:
        # Loop through each itinerary in the route_departure
        for itinerary in route_departure.get('itineraries', []):

            # Append each formatted stop information to the list
            formatted_stops.append({
                'route_short_name': route_departure['route_short_name'],
                'headsign': itinerary['headsign'],  # Now correctly accessing 'headsign' from 'itineraries'
            })

    # Return the filtered and formatted response
    return json.dumps(formatted_stops, indent=4)



def get_nearby_stops_direct(lat, lon, api_key):
    URL = 'https://external.transitapp.com/v3/public/nearby_stops'
    params = {
        'lat': lat,
        'lon': lon,
        'max_distance': '400',  # You can adjust this value based on the required search radius
        'stop_filter': 'Routable'
    }
    headers = {'apiKey': api_key}
    response = requests.get(URL, headers=headers, params=params)
    stops = response.json().get('stops', [])
    #print(stops)
    return [
        {
            'stop_name': stop['stop_name'],
            'distance':stop['distance'],
            'global_stop_id':stop['global_stop_id']
        }
        for stop in stops
    ]
def main():
    openai_api_key =""
    if not openai_api_key:
        print("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
        return
    transit_api_key = "" 
    # Start the chat
    print("Hello! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        # Use OpenAI to understand the user's request (you might need to customize this)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                response_format={ "type": "json_object" },

                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON. Give response NEAR BY STOPS if the user asks about nearby stops,otherwise give response NO."},
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON. Respond with BUS NUMBERS if the user asks for buses from a stop, otherwise give response NO."},
                    {"role": "user", "content": user_input}
                ]
            )
            intent = response.choices[0].message.content
            print(json.loads(intent)["response"])
            answer = json.loads(intent)["response"]
    
            # Check if user is asking for nearby bus stops
            stop_map = {}
            if "NEAR BY STOPS" in answer:
                latitude, longitude = get_user_location()
                if latitude is not None and longitude is not None:
                    buses = get_nearby_stops_direct(latitude, longitude, transit_api_key)
                    stop_map = {bus['stop_name']: bus['global_stop_id'] for bus in buses}
                    print(buses)
                    print("/n /n Stop Map")
                    print(stop_map)
                else:
                    print("Unable to access location.")
            elif "BUS NUMBERS" in answer:
                print("Tell us the bus stop name")
                stopname = input()
                print(stopname)
                # Check if the stop name provided by the user exists in the stop_map
                if stopname in stop_map:
                    global_stop_id = stop_map[stopname]
                    result = get_stop_departure(global_stop_id, transit_api_key)
                    print(result)
                else:
                    print("The specified bus stop name does not exist. Please check the name and try again.")
            else:
                print("I'm sorry, I can only help with finding nearby bus stops.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
